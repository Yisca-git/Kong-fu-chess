from model.board import Board
from model.piece import Piece
from model.position import Position
from rules.piece_rules import PieceRules
from rules.rook_rules import RookRules
from rules.bishop_rules import BishopRules


class QueenRules(PieceRules):
    def __init__(self) -> None:
        self._rook   = RookRules()
        self._bishop = BishopRules()

    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns all squares reachable by combining rook and bishop movement."""
        return self._rook.legal_destinations(board, piece) | self._bishop.legal_destinations(board, piece)
