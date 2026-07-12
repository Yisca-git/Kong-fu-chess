from __future__ import annotations
from model.board import Board
from model.position import Position
from model.piece import Piece
from rules.rules_registry import RULES_BY_KIND
from rules.move_validation import MoveValidation
from rules.sliding import slide


class _BoardWithoutMoving:
    """Board proxy that treats moving-piece origins as empty, so they don't block path checks."""
    def __init__(self, board: Board, moving_origins: set[Position]):
        self._board   = board
        self._origins = moving_origins

    def in_bounds(self, pos: Position) -> bool:
        return self._board.in_bounds(pos)

    def piece_at(self, pos: Position) -> Piece | None:
        if pos in self._origins:
            return None
        return self._board.piece_at(pos)

    def is_empty(self, pos: Position) -> bool:
        return self.piece_at(pos) is None

    def all_pieces(self) -> list[Piece]:
        return self._board.all_pieces()

    @property
    def rows(self) -> int:
        return self._board.rows

    @property
    def cols(self) -> int:
        return self._board.cols


class RuleEngine:
    def validate(
        self,
        board: Board,
        source: Position,
        destination: Position,
        moving_origins: set[Position] | None = None,
        friendly_airborne: set[Position] | None = None,
    ) -> MoveValidation:
        """Validates a requested move against the current board state.
        moving_origins: positions of pieces already in motion — treated as empty for path checks.
        friendly_airborne: positions of friendly airborne pieces — destination is blocked."""
        if not board.in_bounds(source) or not board.in_bounds(destination):
            return MoveValidation(False, "outside_board")

        piece = board.piece_at(source)
        if piece is None:
            return MoveValidation(False, "empty_source")

        occupant = board.piece_at(destination)
        if occupant is not None and occupant.color == piece.color:
            return MoveValidation(False, "friendly_destination")

        if friendly_airborne and destination in friendly_airborne:
            return MoveValidation(False, "friendly_airborne_destination")

        board_view = _BoardWithoutMoving(board, moving_origins or set())
        rules = RULES_BY_KIND[piece.kind]
        if destination not in rules.legal_destinations(board_view, piece):
            return MoveValidation(False, "illegal_piece_move")

        return MoveValidation(True, "ok")
