from abc import ABC, abstractmethod
from model.board import Board
from model.piece import Piece
from model.position import Position


class PieceRules(ABC):
    @abstractmethod
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns all legal destination squares for the given piece on the given board."""
        ...
