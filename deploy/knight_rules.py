from board import Board
from piece import Piece
from position import Position
from piece_rules import PieceRules


_KNIGHT_JUMPS = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]


class KnightRules(PieceRules):
    def legal_destinations(self, board, piece):
        """Returns all squares reachable by L-shaped jumps, ignoring blocking pieces."""
        destinations = set()
        for dr, dc in _KNIGHT_JUMPS:
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
