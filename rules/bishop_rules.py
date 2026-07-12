from model.board import Board
from model.piece import Piece
from model.position import Position
from rules.piece_rules import PieceRules
from rules.sliding import slide


class BishopRules(PieceRules):
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns all squares reachable by sliding diagonally until blocked."""
        return slide(board, piece, [(1, 1), (1, -1), (-1, 1), (-1, -1)])
