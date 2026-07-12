from board import Board
from piece import Piece
from position import Position
from piece_rules import PieceRules
from sliding import slide


class BishopRules(PieceRules):
    def legal_destinations(self, board, piece):
        return slide(board, piece, [(1, 1), (1, -1), (-1, 1), (-1, -1)])
