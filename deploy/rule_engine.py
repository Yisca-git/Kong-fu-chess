from board import Board
from position import Position
from piece import Piece
from rules_registry import RULES_BY_KIND
from move_validation import MoveValidation
from sliding import slide


class _BoardWithoutMoving:
    def __init__(self, board, moving_origins):
        self._board   = board
        self._origins = moving_origins

    def in_bounds(self, pos):
        return self._board.in_bounds(pos)

    def piece_at(self, pos):
        if pos in self._origins:
            return None
        return self._board.piece_at(pos)

    def is_empty(self, pos):
        return self.piece_at(pos) is None

    def all_pieces(self):
        return self._board.all_pieces()

    @property
    def rows(self):
        return self._board.rows

    @property
    def cols(self):
        return self._board.cols


class RuleEngine:
    def validate(self, board, source, destination, moving_origins=None, friendly_airborne=None):
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
