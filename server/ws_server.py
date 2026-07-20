"""WebSocket server for KungFu Chess (Phase A+B+C).

Run:
    py -m server.ws_server

Flow per connection:
  1. Client sends {"auth": "<username>"}
  2. Server replies {"assigned": "waiting", "elo": <n>}
  3. Matchmaking pairs two players → game starts
  4. Commands: "WQe2e4" (move) or "WKe1" (jump)
"""
from __future__ import annotations
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets
from websockets import ServerConnection

from model.position import Position
from server.game_session import GameSession
from server.protocol import decode_command, encode_snapshot
from server.db import init_db, get_user, update_elo
from server.elo import updated_ratings
from server.matchmaking import MatchmakingQueue

HOST = "localhost"
PORT = 8765

TIMEOUT_POLL = 65   # seconds to wait for match (slightly > matchmaking timeout)
POLL_S       = 0.2


class _Game:
    """Holds all state for one active game."""
    def __init__(self, game_id: int, session: GameSession,
                 slots: dict[int, WebSocketServerProtocol],
                 usernames: dict[int, str]) -> None:
        self.game_id   = game_id
        self.session   = session
        self.slots     = slots
        self.usernames = usernames
        self.lock      = asyncio.Lock()

    async def broadcast(self, payload: str) -> None:
        for ws in list(self.slots.values()):
            try:
                await ws.send(payload)
            except Exception:
                pass

    async def close_slot(self, slot: int) -> None:
        async with self.lock:
            self.slots.pop(slot, None)


class ServerState:
    """Single owner of all mutable server state — replaces module-level globals."""

    def __init__(self) -> None:
        self._games:   dict[int, _Game] = {}
        self._counter: int = 0
        self._lock:    asyncio.Lock = asyncio.Lock()
        # ws → asyncio.Event set when the player is assigned to a game
        self._matched: dict[WebSocketServerProtocol, asyncio.Event] = {}
        # ws → game_id + slot once matched
        self._ws_game: dict[WebSocketServerProtocol, tuple[int, int]] = {}
        self.queue:    MatchmakingQueue | None = None

    # ---------------------------------------------------------------- games

    async def create_game(self, white_name: str, white_ws: WebSocketServerProtocol,
                          black_name: str, black_ws: WebSocketServerProtocol) -> None:
        async with self._lock:
            self._counter += 1
            game_id = self._counter

        slots     = {0: white_ws, 1: black_ws}
        usernames = {0: white_name, 1: black_name}

        def _on_state(payload: str) -> None:
            asyncio.get_event_loop().create_task(self._broadcast_game(game_id, payload))

        def _on_game_over(winner: str) -> None:
            asyncio.get_event_loop().create_task(self._settle_elo(game_id, winner))

        session = GameSession(on_state=_on_state, on_game_over=_on_game_over,
                              white_name=white_name, black_name=black_name)
        game = _Game(game_id, session, slots, usernames)

        async with self._lock:
            self._games[game_id] = game
            self._ws_game[white_ws] = (game_id, 0)
            self._ws_game[black_ws] = (game_id, 1)

        session.start()
        print(f"[server] Game {game_id} started: {white_name} vs {black_name}")

        wu = get_user(white_name)
        bu = get_user(black_name)
        await white_ws.send(json.dumps({"assigned": "white", "elo": wu["elo"],
                                        "opponent": black_name, "opponent_elo": bu["elo"]}))
        await black_ws.send(json.dumps({"assigned": "black", "elo": bu["elo"],
                                        "opponent": white_name, "opponent_elo": wu["elo"]}))

        # signal waiting _handle coroutines
        for ws in (white_ws, black_ws):
            if ws in self._matched:
                self._matched[ws].set()

    def get_game(self, game_id: int) -> _Game | None:
        return self._games.get(game_id)

    async def remove_game(self, game_id: int) -> None:
        async with self._lock:
            game = self._games.pop(game_id, None)
        if game:
            for ws in game.slots.values():
                self._ws_game.pop(ws, None)
            print(f"[server] Game {game_id} closed")

    def ws_game(self, ws: WebSocketServerProtocol) -> tuple[int, int] | None:
        return self._ws_game.get(ws)

    # ---------------------------------------------------------------- matchmaking events

    def register_waiting(self, ws: WebSocketServerProtocol) -> asyncio.Event:
        event = asyncio.Event()
        self._matched[ws] = event
        return event

    def unregister_waiting(self, ws: WebSocketServerProtocol) -> None:
        self._matched.pop(ws, None)

    # ---------------------------------------------------------------- ELO

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
        await game.broadcast(json.dumps({
            "elo_update": {white_name: new_w, black_name: new_b}
        }))

    async def _broadcast_game(self, game_id: int, payload: str) -> None:
        game = self._games.get(game_id)
        if game:
            await game.broadcast(payload)


# ------------------------------------------------------------------ connection handler

async def _handle(ws: WebSocketServerProtocol, state: ServerState) -> None:
    # auth
    try:
        raw      = await asyncio.wait_for(ws.recv(), timeout=10)
        auth     = json.loads(raw)
        username = auth.get("auth", "")
        user     = get_user(username)
        if not user:
            await ws.send(json.dumps({"error": "Unknown user. Please register first."}))
            await ws.close()
            return
    except Exception:
        await ws.close(1008, "Auth timeout or invalid message")
        return

    print(f"[server] {username} (ELO {user['elo']}) connected — entering queue")
    await ws.send(json.dumps({"assigned": "waiting", "elo": user["elo"]}))

    # register Event before enqueuing to avoid race
    matched_event = state.register_waiting(ws)
    state.queue.enqueue(username, user["elo"], ws)
    print(f"[server] queue size after enqueue: {len(state.queue._queue)}")

    # wait for match via Event — also abort if ws closes
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
            # timed out or ws closed before match
            state.queue.dequeue(username)
            state.unregister_waiting(ws)
            return
    finally:
        state.unregister_waiting(ws)

    assignment = state.ws_game(ws)
    if assignment is None:
        return
    game_id, slot = assignment

    # in-game loop
    game = state.get_game(game_id)
    if game is None:
        return
    await ws.send(encode_snapshot(game.session.engine.snapshot()))
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
        game = state.get_game(game_id)
        if game:
            await game.close_slot(slot)
            if not game.slots:
                game.session.stop()
                await state.remove_game(game_id)


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
