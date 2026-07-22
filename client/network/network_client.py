"""NetworkClient: pure WebSocket client — no UI dependencies.

Receives snapshots from the server and forwards them via on_snapshot callback.
Sends move/jump commands via send().
"""
from __future__ import annotations
import asyncio
import json
import threading
from typing import Callable

import websockets

from engine.game_snapshot import GameSnapshot
from client.protocol.codec import parse_snapshot, encode_move, encode_jump
from client.network.events import (NetworkEvent, WaitingEvent, MatchedEvent, TimeoutEvent,
                                   EloUpdateEvent, OpponentDisconnectedEvent,
                                   OpponentForfeitedEvent, ErrorEvent)
from client.config import (SERVER_URI, MSG_ERROR, MSG_ASSIGNED, MSG_WAITING,
                           MSG_PIECES, MSG_ELO_UPDATE, MSG_MATCHMAKING_TIMEOUT,
                           MSG_OPPONENT_DISCONNECTED, MSG_OPPONENT_FORFEITED,
                           MSG_RECONNECTED, MSG_COUNTDOWN)

OnSnapshot = Callable[[GameSnapshot], None]
OnEvent    = Callable[[NetworkEvent], None]


class NetworkClient:
    """Pure WebSocket client. Owns no UI — callers inject callbacks."""

    def __init__(self, username: str,
                 on_snapshot: OnSnapshot,
                 on_event:    OnEvent | None = None) -> None:
        self._username    = username
        self._on_snapshot = on_snapshot
        self._on_event    = on_event or (lambda _: None)
        self._game_id:    int | None = None
        self.color:       str | None = None
        self._ws                     = None
        self._loop:       asyncio.AbstractEventLoop | None = None
        self.matched      = threading.Event()
        self.timed_out    = False
        self.user_closed  = False
        self._countdown:  int | None = None
        self._dispatch: dict[str, Callable[[dict], None]] = {
            MSG_ERROR:                 self._on_error,
            MSG_ASSIGNED:              self._on_assigned,
            MSG_MATCHMAKING_TIMEOUT:   self._on_timeout,
            MSG_PIECES:                self._on_pieces,
            MSG_ELO_UPDATE:            self._on_elo_update,
            MSG_OPPONENT_DISCONNECTED: self._on_opponent_disconnected,
            MSG_OPPONENT_FORFEITED:    self._on_opponent_forfeited,
            MSG_COUNTDOWN:             self._on_countdown,
        }

    def send_move(self, color: str, kind: str,
                  sr: int, sc: int, dr: int, dc: int) -> None:
        self._send(encode_move(color, kind, sr, sc, dr, dc))

    def send_jump(self, color: str, kind: str, row: int, col: int) -> None:
        self._send(encode_jump(color, kind, row, col))

    def send_disconnect(self) -> None:
        self._send(json.dumps({"disconnect": True}))

    def _send(self, cmd: str) -> None:
        if self._ws and self._loop:
            asyncio.run_coroutine_threadsafe(self._ws.send(cmd), self._loop)

    def start(self) -> None:
        threading.Thread(target=lambda: asyncio.run(self._run_ws()), daemon=True).start()

    async def _run_ws(self) -> None:
        self._loop = asyncio.get_event_loop()
        auth_msg = json.dumps(
            {"auth": self._username, "rejoin": self._game_id}
            if self._game_id is not None
            else {"auth": self._username}
        )
        try:
            async with websockets.connect(SERVER_URI) as ws:
                self._ws = ws
                await ws.send(auth_msg)
                async for raw in ws:
                    if self.user_closed:
                        break
                    self._handle(json.loads(raw))
        except OSError:
            pass

    def _handle(self, data: dict) -> None:
        for key, handler in self._dispatch.items():
            if key in data:
                handler(data)
                return

    def _on_error(self, data: dict) -> None:
        self._on_event(ErrorEvent(data[MSG_ERROR]))

    def _on_assigned(self, data: dict) -> None:
        if data[MSG_ASSIGNED] == MSG_WAITING:
            self._on_event(WaitingEvent(elo=str(data.get('elo', '?'))))
        else:
            self.color    = data[MSG_ASSIGNED]
            self._game_id = data.get("game_id")
            self._on_event(MatchedEvent(
                color=self.color,
                opponent=data.get('opponent', '?'),
                opp_elo=str(data.get('opponent_elo', '?')),
                reconnected=bool(data.get(MSG_RECONNECTED, False)),
            ))
            self.matched.set()

    def _on_timeout(self, data: dict) -> None:
        self.timed_out = True
        self._on_event(TimeoutEvent())
        self.matched.set()

    def _on_pieces(self, data: dict) -> None:
        self._on_snapshot(parse_snapshot(data, self._countdown))

    def _on_elo_update(self, data: dict) -> None:
        elo = data[MSG_ELO_UPDATE].get(self._username)
        if elo is not None:
            self._on_event(EloUpdateEvent(new_elo=elo))

    def _on_opponent_disconnected(self, data: dict) -> None:
        self._on_event(OpponentDisconnectedEvent())

    def _on_opponent_forfeited(self, data: dict) -> None:
        self._countdown = None
        self._on_event(OpponentForfeitedEvent())

    def _on_countdown(self, data: dict) -> None:
        self._countdown = data[MSG_COUNTDOWN]
