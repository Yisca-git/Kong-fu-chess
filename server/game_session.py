"""GameSession: owns one GameEngine instance and drives its clock via asyncio."""
from __future__ import annotations
import asyncio
import time
from typing import Callable

from rules.rule_engine import RuleEngine
from rules.rules_registry import RULES_BY_KIND
from realtime.real_time_arbiter import RealTimeArbiter
from engine.game_engine import GameEngine
from engine.arrival_resolver import ArrivalResolver
from engine.score_keeper import ScoreKeeper
from view.setup import build_starting_board
from server.protocol import encode_snapshot

TICK_MS = 33  # ~30 fps game-loop tick


class GameSession:
    """Runs the game clock and notifies a broadcast callback each tick."""

    def __init__(self, on_state: Callable[[str], None],
                 on_game_over: Callable[[str], None] | None = None,
                 white_name: str = "Player 1", black_name: str = "Player 2"):
        self._on_state     = on_state
        self._on_game_over = on_game_over
        board, _pieces = build_starting_board()
        score_keeper   = ScoreKeeper()
        arbiter        = RealTimeArbiter()
        rule_engine    = RuleEngine()
        resolver       = ArrivalResolver(board, RULES_BY_KIND, arbiter, score_keeper)
        self._engine   = GameEngine(board, rule_engine, arbiter, resolver, score_keeper,
                                    white_name=white_name, black_name=black_name)
        self._task: asyncio.Task | None = None

    @property
    def engine(self) -> GameEngine:
        return self._engine

    def start(self) -> None:
        self._task = asyncio.get_event_loop().create_task(self._loop())

    def stop(self) -> None:
        if self._task:
            self._task.cancel()

    async def _loop(self) -> None:
        last = time.monotonic()
        while not self._engine.game_over:
            await asyncio.sleep(TICK_MS / 1000)
            now     = time.monotonic()
            elapsed = int((now - last) * 1000)
            last    = now
            if elapsed > 0:
                self._engine.advance_time(elapsed)
            self._on_state(encode_snapshot(self._engine.snapshot()))
        # send final snapshot with game_over=True so clients close their windows
        self._on_state(encode_snapshot(self._engine.snapshot()))
        if self._on_game_over and self._engine.snapshot().winner:
            self._on_game_over(self._engine.snapshot().winner)
