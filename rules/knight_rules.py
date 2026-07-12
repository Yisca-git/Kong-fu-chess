from model.board import Board
from model.piece import Piece
from model.position import Position
from rules.piece_rules import PieceRules


_KNIGHT_JUMPS = [(2, 1), (2, -1), (-2, 1), (-2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2)]


class KnightRules(PieceRules):
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns all squares reachable by L-shaped jumps, ignoring blocking pieces."""
        destinations = set()
        for dr, dc in _KNIGHT_JUMPS:
            pos = Position(piece.cell.row + dr, piece.cell.col + dc)
            if not board.in_bounds(pos):
                continue
            occupant = board.piece_at(pos)
            if occupant is None or occupant.color != piece.color:
                destinations.add(pos)
        return destinations
