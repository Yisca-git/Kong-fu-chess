from board import Board
from piece import Piece
from position import Position
from piece_rules import PieceRules


_KING_STEPS = [(dr, dc) for dr in (-1, 0, 1) for dc in (-1, 0, 1) if (dr, dc) != (0, 0)]


class KingRules(PieceRules):
    def legal_destinations(self, board, piece):
        """Returns all squares one step away in any direction."""
        destinations = set()
        for dr, dc in _KING_STEPS:
            r, c = piece.cell.row + dr, piece.cell.col + dc
            if r < 0 or c < 0:
                continue
            pos = Position(r, c)
            if not board.in_bounds(pos):
                continue
            occupant = board.piece_at(pos)
            if occupant is None or occupant.color != piece.color:
                destinations.add(pos)
        return destinations
