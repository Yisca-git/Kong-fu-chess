"""Reconnection grace-period manager (Phase D).

When a player disconnects mid-game, a countdown of GRACE_S seconds starts.
If the player reconnects within that window, the timer is cancelled.
If not, on_forfeit(game_id, slot) is called.
"""
from __future__ import annotations
import asyncio
from typing import Callable, Awaitable

GRACE_S = 25

OnForfeit = Callable[[int, int], Awaitable[None]]


class ReconnectManager:
    def __init__(self, on_forfeit: OnForfeit) -> None:
        self._on_forfeit = on_forfeit
        self._timers: dict[tuple[int, int], asyncio.Task] = {}  # (game_id, slot) → task

    def start_timer(self, game_id: int, slot: int) -> None:
        key = (game_id, slot)
        if key in self._timers:
            return
        print(f"[reconnect] game {game_id} slot {slot} — grace period started ({GRACE_S}s)")
        self._timers[key] = asyncio.get_event_loop().create_task(
            self._countdown(game_id, slot)
        )

    def cancel_timer(self, game_id: int, slot: int) -> bool:
        """Returns True if a timer was active and cancelled."""
        key = (game_id, slot)
        task = self._timers.pop(key, None)
        if task:
            task.cancel()
            print(f"[reconnect] game {game_id} slot {slot} — reconnected in time")
            return True
        return False

    def has_timer(self, game_id: int, slot: int) -> bool:
        return (game_id, slot) in self._timers

    async def _countdown(self, game_id: int, slot: int) -> None:
        try:
            await asyncio.sleep(GRACE_S)
            self._timers.pop((game_id, slot), None)
            print(f"[reconnect] game {game_id} slot {slot} — grace expired, forfeit")
            await self._on_forfeit(game_id, slot)
        except asyncio.CancelledError:
            pass
