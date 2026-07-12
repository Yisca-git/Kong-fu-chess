from __future__ import annotations
from typing import TYPE_CHECKING
from model.board import Board
from model.position import Position
from rules.rule_engine import RuleEngine
from engine.move_result import MoveResult
from engine.game_snapshot import GameSnapshot

if TYPE_CHECKING:
    from realtime.real_time_arbiter import RealTimeArbiter


class GameEngine:
    def __init__(self, board: Board, rule_engine: RuleEngine, arbiter: RealTimeArbiter):
        self._board       = board
        self._rule_engine = rule_engine
        self._arbiter     = arbiter
        self.game_over    = False

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """Validates and initiates a move request. Returns MoveResult with outcome reason."""
        if self.game_over:
            return MoveResult(False, "game_over")

        if self._arbiter.has_active_motion():
            return MoveResult(False, "motion_in_progress")

        validation = self._rule_engine.validate(self._board, source, destination)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        self._arbiter.start_motion(self._board.piece_at(source), destination)
        return MoveResult(True, "ok")

    def advance_time(self, ms: int) -> None:
        """Advances the game clock and resolves arrivals via the arbiter."""
        king_captured = self._arbiter.advance_time(ms)
        if king_captured:
            self.game_over = True

    def piece_at(self, pos: Position) -> bool:
        """Returns True if a piece exists at the given position. Used by Controller to check for empty cells."""
        return self._board.piece_at(pos) is not None

    def snapshot(self) -> GameSnapshot:
        """Returns a read-only snapshot of the current game state."""
        return GameSnapshot.from_pieces(
            self._board.all_pieces(),
            self.game_over,
            self._board.rows,
            self._board.cols,
        )
