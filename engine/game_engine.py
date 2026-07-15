from __future__ import annotations
from typing import TYPE_CHECKING
from model.board import Board
from model.position import Position
from rules.rule_engine import RuleEngine
from engine.move_result import MoveResult
from engine.game_snapshot import GameSnapshot
from engine.arrival_resolver import ArrivalResolver

if TYPE_CHECKING:
    from realtime.real_time_arbiter import RealTimeArbiter


class GameEngine:
    def __init__(self, board: Board, rule_engine: RuleEngine, arbiter: RealTimeArbiter, resolver: ArrivalResolver):
        self._board       = board
        self._rule_engine = rule_engine
        self._arbiter     = arbiter
        self._resolver    = resolver
        self.game_over    = False

    def request_move(self, source: Position, destination: Position) -> MoveResult:
        """Validates and initiates a move request. Returns MoveResult with outcome reason."""
        if self.game_over:
            return MoveResult(False, MoveResult.GAME_OVER)

        piece = self._board.piece_at(source)
        if piece is None:
            return MoveResult(False, MoveResult.EMPTY_SOURCE)

        if self._arbiter.is_piece_moving(piece):
            return MoveResult(False, MoveResult.PIECE_ALREADY_MOVING)

        if self._arbiter.is_piece_on_cooldown(piece):
            return MoveResult(False, MoveResult.PIECE_ON_COOLDOWN)

        moving_origins    = self._arbiter.moving_origins()
        friendly_airborne = self._arbiter.friendly_airborne_cells(piece.color)
        validation        = self._rule_engine.validate(self._board, source, destination, moving_origins, friendly_airborne)
        if not validation.is_valid:
            return MoveResult(False, validation.reason)

        self._arbiter.start_motion(piece, destination)
        return MoveResult(True, MoveResult.OK)

    def request_jump(self, pos: Position) -> MoveResult:
        """Validates and initiates a jump request. Returns MoveResult with outcome reason."""
        if self.game_over:
            return MoveResult(False, MoveResult.GAME_OVER)

        if self._arbiter.is_piece_airborne_at(pos):
            return MoveResult(False, MoveResult.PIECE_ALREADY_AIRBORNE)

        piece = self._board.piece_at(pos)
        if piece is None:
            return MoveResult(False, MoveResult.EMPTY_SOURCE)

        if self._arbiter.is_piece_moving(piece):
            return MoveResult(False, MoveResult.PIECE_ALREADY_MOVING)

        if self._arbiter.is_piece_on_cooldown(piece):
            return MoveResult(False, MoveResult.PIECE_ON_COOLDOWN)

        self._board.remove_piece(pos)
        self._arbiter.start_jump(piece)
        return MoveResult(True, MoveResult.OK)

    def advance_time(self, ms: int) -> None:
        """Advances the game clock. The arbiter tracks timing only; the resolver applies
        every due arrival/landing to the board."""
        if self._arbiter.advance_time(ms, self._resolver):
            self.game_over = True

    def piece_at(self, pos: Position) -> bool:
        """Returns True if a piece exists at the given position. Used by Controller to check for empty cells."""
        return self._board.piece_at(pos) is not None

    def snapshot(self) -> GameSnapshot:
        """Returns a read-only snapshot of the current game state, including airborne pieces."""
        return GameSnapshot.from_pieces(
            self._board.all_pieces() + self._arbiter.airborne_pieces(),
            self.game_over,
            self._board.rows,
            self._board.cols,
        )
