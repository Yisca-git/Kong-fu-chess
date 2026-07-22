"""ServerState: tracks all active games, waiting connections, and user mappings."""
from __future__ import annotations
import asyncio
import json
from typing import Callable
from websockets import ServerConnection

from server.core.game import Game
from server.core.game_session import GameSession
from server.db.db import get_user, log_event, update_elo
from server.services.elo import updated_ratings
from server.services.matchmaking import MatchmakingQueue
from server.services.reconnect import ReconnectManager
from server.network.protocol import encode_snapshot
from engine.game_snapshot import GameSnapshot


class ServerState:
    def __init__(self) -> None:
        self._games:     dict[int, Game] = {}
        self._counter:   int = 0
        self._lock:      asyncio.Lock = asyncio.Lock()
        self._matched:   dict[ServerConnection, asyncio.Event] = {}
        self._ws_game:   dict[ServerConnection, tuple[int, int]] = {}
        self._user_game: dict[str, tuple[int, int]] = {}
        self._settled:   set[int] = set()
        self.queue:      MatchmakingQueue | None = None
        self.reconnect:  ReconnectManager = ReconnectManager(on_forfeit=self._forfeit,
                                                               on_tick=self._on_countdown_tick)

    async def create_game(self, white_name: str, white_ws: ServerConnection,
                          black_name: str, black_ws: ServerConnection) -> None:
        async with self._lock:
            self._counter += 1
            game_id = self._counter

        def _on_state(snap: GameSnapshot) -> None:
            asyncio.get_running_loop().create_task(self._broadcast_game(game_id, snap))

        def _on_game_over(winner: str) -> None:
            asyncio.get_running_loop().create_task(self._on_game_over_task(game_id, winner))

        session = GameSession(on_state=_on_state, on_game_over=_on_game_over,
                              white_name=white_name, black_name=black_name)
        game = Game(game_id, session, {0: white_name, 1: black_name})

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

    def get_game(self, game_id: int) -> Game | None:
        return self._games.get(game_id)

    def find_user_game(self, username: str) -> tuple[int, int] | None:
        return self._user_game.get(username)

    def ws_game(self, ws: ServerConnection) -> tuple[int, int] | None:
        return self._ws_game.get(ws)

    def register_waiting(self, ws: ServerConnection) -> asyncio.Event:
        event = asyncio.Event()
        self._matched[ws] = event
        return event

    def unregister_waiting(self, ws: ServerConnection) -> None:
        self._matched.pop(ws, None)

    def register_ws_game(self, ws: ServerConnection, game_id: int, slot: int) -> None:
        """Records the ws→(game_id, slot) mapping under the state lock."""
        asyncio.get_running_loop().create_task(self._register_ws_game(ws, game_id, slot))

    async def _register_ws_game(self, ws: ServerConnection, game_id: int, slot: int) -> None:
        async with self._lock:
            self._ws_game[ws] = (game_id, slot)

    def deregister_ws_game(self, ws: ServerConnection) -> None:
        self._ws_game.pop(ws, None)

    def list_games(self) -> list[dict]:
        return [
            {"game_id": g.game_id,
             "white": g.usernames.get(0, "?"),
             "black": g.usernames.get(1, "?")}
            for g in self._games.values()
        ]

    async def remove_game(self, game_id: int) -> None:
        async with self._lock:
            game = self._games.pop(game_id, None)
        if game:
            for ws in list(game.slots.values()):
                self._ws_game.pop(ws, None)
            for name in game.usernames.values():
                self._user_game.pop(name, None)
            self._settled.discard(game_id)
            print(f"[server] Game {game_id} closed")

    async def _broadcast_game(self, game_id: int, snap: GameSnapshot) -> None:
        game = self._games.get(game_id)
        if game:
            await game.broadcast(encode_snapshot(snap))

    async def _on_countdown_tick(self, game_id: int, slot: int, seconds_left: int) -> None:
        game = self._games.get(game_id)
        if not game:
            return
        opp_ws = game.slots.get(1 - slot)
        if opp_ws:
            try:
                await opp_ws.send(json.dumps({"countdown": seconds_left}))
            except OSError:
                pass

    async def _forfeit(self, game_id: int, slot: int) -> None:
        game = self._games.get(game_id)
        if not game or game.session.engine.game_over or game.forfeited:
            return
        game.forfeited = True
        winner_slot = 1 - slot
        winner = "w" if winner_slot == 0 else "b"
        print(f"[server] Game {game_id}: slot {slot} forfeited, winner slot {winner_slot}")
        log_event(game_id, "forfeit", f"slot={slot} forfeited")
        ws = game.slots.get(winner_slot)
        print(f"[server] winner ws={ws}, slots={list(game.slots.keys())}")
        if ws:
            try:
                await ws.send(json.dumps({"opponent_forfeited": True}))
            except OSError:
                pass
        await self._settle_elo(game_id, winner)
        snap = game.session.engine.snapshot()
        await game.broadcast(encode_snapshot(snap, force_game_over=True, winner=winner))
        game.session.stop()
        if ws:
            try:
                await ws.close()
            except OSError:
                pass

    async def _on_game_over_task(self, game_id: int, winner: str) -> None:
        await self._settle_elo(game_id, winner)
        game = self._games.get(game_id)
        if game:
            for ws in list(game.slots.values()) + list(game.spectators):
                try:
                    await ws.close()
                except OSError:
                    pass
            await self.remove_game(game_id)

    async def _settle_elo(self, game_id: int, winner: str) -> None:
        if game_id in self._settled:
            return
        self._settled.add(game_id)
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
        print(f"[server] ELO -- {white_name}: {wu['elo']}->{new_w}  "
              f"{black_name}: {bu['elo']}->{new_b}")
        log_event(game_id, "game_over",
                  f"winner={winner} {white_name}:{new_w} {black_name}:{new_b}")
        await game.broadcast_raw(json.dumps({"elo_update": {white_name: new_w, black_name: new_b}}))
