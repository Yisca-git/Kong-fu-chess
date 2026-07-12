from abc import ABC, abstractmethod
from board import Board
from piece import Piece
from position import Position


class PieceRules(ABC):
    @abstractmethod
    def legal_destinations(self, board, piece):
        ...

    def on_arrival(self, piece, board_rows):
        pass
