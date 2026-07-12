from model.board import Board
from model.piece import Piece
from model.position import Position
from rules.piece_rules import PieceRules
from rules.sliding import slide


class RookRules(PieceRules):
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns all squares reachable by sliding horizontally or vertically until blocked."""
        return slide(board, piece, [(0, 1), (0, -1), (1, 0), (-1, 0)])
