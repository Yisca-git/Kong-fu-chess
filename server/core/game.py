"""Game: holds one active game's session, connections, and spectators."""
from __future__ import annotations
import asyncio
from websockets import ServerConnection
from server.core.game_session import GameSession


class Game:
    def __init__(self, game_id: int, session: GameSession,
                 usernames: dict[int, str]) -> None:
        self.game_id     = game_id
        self.session     = session
        self.usernames   = usernames
        self.slots:      dict[int, ServerConnection] = {}
        self.spectators: set[ServerConnection] = set()
        self.lock        = asyncio.Lock()
        self._ready_count = 0
        self._ready_event = asyncio.Event()

    async def broadcast(self, payload: str) -> None:
        for ws in list(self.slots.values()) + list(self.spectators):
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
