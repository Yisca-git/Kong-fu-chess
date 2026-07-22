"""Matchmaking queue for KungFu Chess (Phase C).

Flow:
  1. Player calls enqueue(username, elo, ws) after login.
  2. The scanner task runs every second, pairing players within ELO_DELTA.
  3. If no match is found within TIMEOUT_S seconds the player is removed
     and receives a "matchmaking_timeout" message.
  4. On a successful match, on_match(username_white, ws_white,
                                    username_black, ws_black) is called.
"""
from __future__ import annotations
import asyncio
import time
from dataclasses import dataclass, field
from typing import Callable, Awaitable

from websockets import ServerConnection

ELO_DELTA  = 100
TIMEOUT_S  = 60
SCAN_S     = 1.0


@dataclass
class _Entry:
    username:  str
    elo:       int
    ws:        ServerConnection
    joined_at: float = field(default_factory=time.monotonic)


OnMatch = Callable[
    [str, ServerConnection, str, ServerConnection],
    Awaitable[None],
]


class MatchmakingQueue:
    def __init__(self, on_match: OnMatch) -> None:
        self._queue:    list[_Entry] = []
        self._on_match  = on_match
        self._task:     asyncio.Task | None = None

    def start(self) -> None:
        self._task = asyncio.get_running_loop().create_task(self._scan_loop())

    def stop(self) -> None:
        if self._task:
            self._task.cancel()

    def enqueue(self, username: str, elo: int, ws: ServerConnection) -> None:
        # prevent duplicate entries
        self._queue = [e for e in self._queue if e.username != username]
        self._queue.append(_Entry(username, elo, ws))
        print(f"[matchmaking] {username} (ELO {elo}) joined queue ({len(self._queue)} waiting)")

    def dequeue(self, username: str) -> None:
        self._queue = [e for e in self._queue if e.username != username]

    async def _scan_loop(self) -> None:
        while True:
            await asyncio.sleep(SCAN_S)
            await self._expire_timeouts()
            await self._try_match()

    async def _expire_timeouts(self) -> None:
        now     = time.monotonic()
        expired = [e for e in self._queue if now - e.joined_at >= TIMEOUT_S]
        for e in expired:
            self._queue.remove(e)
            print(f"[matchmaking] {e.username} timed out")
            try:
                await e.ws.send('{"matchmaking_timeout": true}')
            except OSError:
                pass

    async def _try_match(self) -> None:
        if len(self._queue) < 2:
            return
        # sort by ELO so closest pairs are adjacent
        self._queue.sort(key=lambda e: e.elo)
        i = 0
        while i < len(self._queue) - 1:
            a = self._queue[i]
            b = self._queue[i + 1]
            if abs(a.elo - b.elo) <= ELO_DELTA:
                self._queue.pop(i + 1)
                self._queue.pop(i)
                print(f"[matchmaking] Matched {a.username} vs {b.username}")
                await self._on_match(a.username, a.ws, b.username, b.ws)
                # restart scan after mutation
                return
            i += 1
