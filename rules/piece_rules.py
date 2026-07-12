from abc import ABC, abstractmethod
from model.board import Board
from model.piece import Piece
from model.position import Position


class PieceRules(ABC):
    @abstractmethod
    def legal_destinations(self, board: Board, piece: Piece) -> set[Position]:
        """Returns all legal destination squares for the given piece on the given board."""
        ...

    def on_arrival(self, piece: Piece, board_rows: int) -> None:
        """Called when a piece arrives at its destination. Override to add post-move behaviour."""
        pass
