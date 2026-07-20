"""WebSocket server for KungFu Chess (Phase A+B+C+D)."""
from __future__ import annotations
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets
from websockets import ServerConnection
from websockets.connection import State as WsState

from model.position import Position
from server.game_session import GameSession
from server.protocol import decode_command, encode_snapshot
from server.db import init_db, get_user, update_elo, log_event, get_all_users
from server.elo import updated_ratings
from server.matchmaking import MatchmakingQueue
from server.reconnect import ReconnectManager

HOST = "localhost"
PORT = 8765
TIMEOUT_POLL = 65


class _Game:
    def __init__(self, game_id: int, session: GameSession,
                 usernames: dict[int, str]) -> None:
        self.game_id    = game_id
        self.session    = session
        self.usernames  = usernames
        self.slots:     dict[int, ServerConnection] = {}
        self.spectators: set[ServerConnection] = set()
        self.lock       = asyncio.Lock()
        self._ready_count = 0
        self._ready_event = asyncio.Event()

    async def broadcast(self, payload: str) -> None:
        targets = list(self.slots.values()) + list(self.spectators)
        for ws in targets:
            try:
                await ws.send(payload)
            except Exception:
                pass

    async def set_slot(self, slot: int, ws: ServerConnection) -> None:
        async with self.lock:
            self.slots[slot] = ws
            self._ready_count += 1
            if self._ready_count >= 2:
                self._ready_event.set()

    async def clear_slot(self, slot: int) -> None:
        async with self.lock:
            self.slots.pop(slot, None)

    async def wait_ready(self, timeout: float = 10.0) -> bool:
        try:
            await asyncio.wait_for(self._ready_event.wait(), timeout=timeout)
            return True
        except asyncio.TimeoutError:
            return False


class ServerState:
    def __init__(self) -> None:
        self._games:     dict[int, _Game] = {}
        self._counter:   int = 0
        self._lock:      asyncio.Lock = asyncio.Lock()
        self._matched:   dict[ServerConnection, asyncio.Event] = {}
        self._ws_game:   dict[ServerConnection, tuple[int, int]] = {}
        self._user_game: dict[str, tuple[int, int]] = {}
        self.queue:      MatchmakingQueue | None = None
        self.reconnect:  ReconnectManager = ReconnectManager(on_forfeit=self._forfeit)

    async def create_game(self, white_name: str, white_ws: ServerConnection,
                          black_name: str, black_ws: ServerConnection) -> None:
        async with self._lock:
            self._counter += 1
            game_id = self._counter

        usernames = {0: white_name, 1: black_name}

        def _on_state(payload: str) -> None:
            asyncio.get_event_loop().create_task(self._broadcast_game(game_id, payload))

        def _on_game_over(winner: str) -> None:
            asyncio.get_event_loop().create_task(self._on_game_over_task(game_id, winner))

        session = GameSession(on_state=_on_state, on_game_over=_on_game_over,
                              white_name=white_name, black_name=black_name)
        game = _Game(game_id, session, usernames)

        async with self._lock:
            self._games[game_id] = game
            self._ws_game[white_ws] = (game_id, 0)
            self._ws_game[black_ws] = (game_id, 1)
            self._user_game[white_name] = (game_id, 0)
            self._user_game[black_name] = (game_id, 1)

        print(f"[server] Game {game_id} created: {white_name} vs {black_name}")
        log_event(game_id, "game_start", f"{white_name} vs {black_name}")

        wu = get_user(white_name)
        bu = get_user(black_name)
        await white_ws.send(json.dumps({"assigned": "white", "elo": wu["elo"],
                                        "game_id": game_id,
                                        "opponent": black_name, "opponent_elo": bu["elo"]}))
        await black_ws.send(json.dumps({"assigned": "black", "elo": bu["elo"],
                                        "game_id": game_id,
                                        "opponent": white_name, "opponent_elo": wu["elo"]}))
        for ws in (white_ws, black_ws):
            if ws in self._matched:
                self._matched[ws].set()

    def get_game(self, game_id: int) -> _Game | None:
        return self._games.get(game_id)

    def find_user_game(self, username: str) -> tuple[int, int] | None:
        return self._user_game.get(username)

    async def remove_game(self, game_id: int) -> None:
        async with self._lock:
            game = self._games.pop(game_id, None)
        if game:
            for ws in list(game.slots.values()):
                self._ws_game.pop(ws, None)
            for name in game.usernames.values():
                self._user_game.pop(name, None)
            print(f"[server] Game {game_id} closed")

    def ws_game(self, ws: ServerConnection) -> tuple[int, int] | None:
        return self._ws_game.get(ws)

    def register_waiting(self, ws: ServerConnection) -> asyncio.Event:
        event = asyncio.Event()
        self._matched[ws] = event
        return event

    def unregister_waiting(self, ws: ServerConnection) -> None:
        self._matched.pop(ws, None)

    async def _forfeit(self, game_id: int, slot: int) -> None:
        game = self._games.get(game_id)
        if not game or game.session.engine.game_over:
            return
        winner_slot = 1 - slot
        winner = "w" if winner_slot == 0 else "b"
        print(f"[server] Game {game_id}: slot {slot} forfeited")
        log_event(game_id, "forfeit", f"slot={slot} forfeited")
        ws = game.slots.get(winner_slot)
        if ws:
            try:
                await ws.send(json.dumps({"opponent_forfeited": True}))
            except Exception:
                pass
        await self._settle_elo(game_id, winner)
        # send a game_over snapshot so the winner's window closes
        snap = encode_snapshot(game.session.engine.snapshot(), force_game_over=True,
                               winner=winner)
        if ws:
            try:
                await ws.send(snap)
                await ws.close()
            except Exception:
                pass
        for spec in list(game.spectators):
            try:
                await spec.send(snap)
                await spec.close()
            except Exception:
                pass
        game.session.stop()
        await self.remove_game(game_id)

    async def _on_game_over_task(self, game_id: int, winner: str) -> None:
        await self._settle_elo(game_id, winner)
        game = self._games.get(game_id)
        if game:
            for ws in list(game.slots.values()) + list(game.spectators):
                try:
                    await ws.close()
                except Exception:
                    pass

    async def _settle_elo(self, game_id: int, winner: str) -> None:
        game = self._games.get(game_id)
        if not game:
            return
        white_name = game.usernames.get(0)
        black_name = game.usernames.get(1)
        if not white_name or not black_name:
            return
        wu = get_user(white_name)
        bu = get_user(black_name)
        if not wu or not bu:
            return
        if winner == "w":
            new_w, new_b = updated_ratings(wu["elo"], bu["elo"])
        else:
            new_b, new_w = updated_ratings(bu["elo"], wu["elo"])
        update_elo(white_name, new_w)
        update_elo(black_name, new_b)
        print(f"[server] ELO — {white_name}: {wu['elo']}→{new_w}  "
              f"{black_name}: {bu['elo']}→{new_b}")
        log_event(game_id, "game_over", f"winner={winner} {white_name}:{new_w} {black_name}:{new_b}")
        await game.broadcast(json.dumps({
            "elo_update": {white_name: new_w, black_name: new_b}
        }))

    def list_games(self) -> list[dict]:
        return [
            {"game_id": g.game_id,
             "white": g.usernames.get(0, "?"),
             "black": g.usernames.get(1, "?")}
            for g in self._games.values()
        ]

    async def _broadcast_game(self, game_id: int, payload: str) -> None:
        game = self._games.get(game_id)
        if game:
            await game.broadcast(payload)


async def _watch_game(ws: ServerConnection, state: ServerState, game_id: int,
                      username: str) -> None:
    game = state.get_game(game_id)
    if game is None:
        await ws.send(json.dumps({"error": "Game not found."}))
        await ws.close()
        return
    async with game.lock:
        game.spectators.add(ws)
    print(f"[server] {username} watching game {game_id}")
    # send current snapshot immediately
    await ws.send(encode_snapshot(game.session.engine.snapshot()))
    try:
        await ws.wait_closed()
    finally:
        async with game.lock:
            game.spectators.discard(ws)
        print(f"[server] {username} stopped watching game {game_id}")


async def _play_game(ws: ServerConnection, state: ServerState,
                     game_id: int, slot: int) -> None:
    game = state.get_game(game_id)
    if game is None:
        return

    state.reconnect.cancel_timer(game_id, slot)
    await game.set_slot(slot, ws)
    async with state._lock:
        state._ws_game[ws] = (game_id, slot)

    # wait for both handlers to be ready, then start session once
    if await game.wait_ready():
        if not game.session._task:
            game.session.start()
            print(f"[server] Game {game_id} started")
            await game.broadcast(encode_snapshot(game.session.engine.snapshot()))
    else:
        return

    try:
        async for message in ws:
            game = state.get_game(game_id)
            if game is None:
                break
            try:
                _color, src, dst = decode_command(message)
                src_pos = Position(*src)
                if dst is None:
                    result = game.session.engine.request_jump(src_pos)
                else:
                    result = game.session.engine.request_move(src_pos, Position(*dst))
                if not result.is_accepted:
                    await ws.send(json.dumps({"rejection": result.reason}))
            except Exception as e:
                await ws.send(json.dumps({"error": str(e)}))
    finally:
        print(f"[server] slot {slot} disconnected from game {game_id}")
        state._ws_game.pop(ws, None)
        game = state.get_game(game_id)
        if game:
            await game.clear_slot(slot)
            if game.session.engine.game_over:
                # close the other connection so its handler exits too
                opp_ws = game.slots.get(1 - slot)
                if opp_ws:
                    try:
                        await opp_ws.close()
                    except Exception:
                        pass
                game.session.stop()
                await state.remove_game(game_id)
            else:
                state.reconnect.start_timer(game_id, slot)
                opp_ws = game.slots.get(1 - slot)
                if opp_ws:
                    try:
                        await opp_ws.send(json.dumps({"opponent_disconnected": True}))
                    except Exception:
                        pass


async def _handle(ws: ServerConnection, state: ServerState) -> None:
    try:
        raw  = await asyncio.wait_for(ws.recv(), timeout=10)
        auth = json.loads(raw)
    except Exception:
        await ws.close(1008, "Auth timeout")
        return

    username = auth.get("auth", "")
    user     = get_user(username)
    if not user:
        await ws.send(json.dumps({"error": "Unknown user. Please register first."}))
        await ws.close()
        return

    # list games path
    if auth.get("list_games"):
        games = state.list_games()
        await ws.send(json.dumps({"games": games}))
        await ws.close()
        return

    # watch path
    watch_id = auth.get("watch")
    if watch_id is not None:
        await _watch_game(ws, state, watch_id, username)
        return

    # reconnect path
    rejoin_id = auth.get("rejoin")
    if rejoin_id is not None:
        assignment = state.find_user_game(username)
        if assignment and assignment[0] == rejoin_id:
            game_id, slot = assignment
            game = state.get_game(game_id)
            if game and state.reconnect.has_timer(game_id, slot):
                print(f"[server] {username} reconnected to game {game_id}")
                color = "white" if slot == 0 else "black"
                await ws.send(json.dumps({"assigned": color, "elo": user["elo"],
                                          "game_id": game_id, "reconnected": True}))
                await _play_game(ws, state, game_id, slot)
                return
        await ws.send(json.dumps({"error": "No active game to rejoin."}))
        await ws.close()
        return

    # new game path
    print(f"[server] {username} (ELO {user['elo']}) connected — entering queue")
    await ws.send(json.dumps({"assigned": "waiting", "elo": user["elo"]}))

    matched_event = state.register_waiting(ws)
    state.queue.enqueue(username, user["elo"], ws)

    try:
        wait_match = asyncio.ensure_future(matched_event.wait())
        wait_close = asyncio.ensure_future(ws.wait_closed())
        done, pending = await asyncio.wait(
            [wait_match, wait_close],
            timeout=TIMEOUT_POLL,
            return_when=asyncio.FIRST_COMPLETED,
        )
        for t in pending:
            t.cancel()
        if not done or wait_match not in done:
            state.queue.dequeue(username)
            state.unregister_waiting(ws)
            return
    finally:
        state.unregister_waiting(ws)

    assignment = state.ws_game(ws)
    if assignment is None:
        return
    game_id, slot = assignment

    if ws.state != WsState.OPEN:
        game = state.get_game(game_id)
        if game:
            await game.clear_slot(slot)
            state.reconnect.start_timer(game_id, slot)
        return

    await _play_game(ws, state, game_id, slot)


async def main() -> None:
    init_db()
    state = ServerState()
    state.queue = MatchmakingQueue(on_match=state.create_game)
    state.queue.start()
    print(f"[server] Listening on ws://{HOST}:{PORT}")
    async with websockets.serve(lambda ws: _handle(ws, state), HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
