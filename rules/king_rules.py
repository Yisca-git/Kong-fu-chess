from model.board import Board
from model.piece import Piece
from model.position import Position
from rules.piece_rules import PieceRules


_KING_STEPS = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]


class KingRules(PieceRules):
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns all squares one step away in any direction."""
        destinations = set()
        for dr, dc in _KING_STEPS:
            pos = Position(piece.cell.row + dr, piece.cell.col + dc)
            if not board.in_bounds(pos):
                continue
            occupant = board.piece_at(pos)
            if occupant is None or occupant.color != piece.color:
                destinations.add(pos)
        return destinations
