from model.board import Board
from model.position import Position
from rules.rules_registry import RULES_BY_KIND
from rules.move_validation import MoveValidation


class RuleEngine:
    def validate(self, board: Board, source: Position, destination: Position) -> MoveValidation:
        """Validates a requested move against the current board state."""
        if not board.in_bounds(source) or not board.in_bounds(destination):
            return MoveValidation(False, "outside_board")

        piece = board.piece_at(source)
        if piece is None:
            return MoveValidation(False, "empty_source")

        occupant = board.piece_at(destination)
        if occupant is not None and occupant.color == piece.color:
            return MoveValidation(False, "friendly_destination")

        rules = RULES_BY_KIND[piece.kind]
        if destination not in rules.legal_destinations(board, piece):
            return MoveValidation(False, "illegal_piece_move")

        return MoveValidation(True, "ok")
