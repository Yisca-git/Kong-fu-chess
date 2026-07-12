from position import Position
from piece import Piece


class Board:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self._cells = {}

    def in_bounds(self, pos):
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def piece_at(self, pos):
        return self._cells.get(pos)

    def is_empty(self, pos):
        return pos not in self._cells

    def add_piece(self, piece):
        if piece.cell in self._cells:
            raise ValueError("Cell {} is already occupied".format(piece.cell))
        self._cells[piece.cell] = piece

    def remove_piece(self, pos):
        if pos not in self._cells:
            raise ValueError("No piece at {}".format(pos))
        return self._cells.pop(pos)

    def move_piece(self, piece, destination):
        if destination in self._cells:
            raise ValueError("Cell {} is already occupied".format(destination))
        del self._cells[piece.cell]
        piece.cell = destination
        self._cells[destination] = piece

    def all_pieces(self):
        return list(self._cells.values())
