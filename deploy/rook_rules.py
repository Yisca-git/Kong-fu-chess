from board import Board
from piece import Piece
from position import Position
from piece_rules import PieceRules
from sliding import slide


class RookRules(PieceRules):
    def legal_destinations(self, board, piece):
        """Returns all squares reachable by sliding horizontally or vertically until blocked."""
        return slide(board, piece, [(0, 1), (0, -1), (1, 0), (-1, 0)])
