from board import Board
from piece import Piece
from position import Position
from piece_rules import PieceRules
from rook_rules import RookRules
from bishop_rules import BishopRules


class QueenRules(PieceRules):
    def legal_destinations(self, board, piece):
        """Returns all squares reachable by combining rook and bishop movement."""
        return RookRules().legal_destinations(board, piece) | BishopRules().legal_destinations(board, piece)
