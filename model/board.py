from model.position import Position
from model.piece import Piece


class Board:
    def __init__(self, rows: int, cols: int):
        self.rows = rows
        self.cols = cols
        self._cells: dict[Position, Piece] = {}

    def in_bounds(self, pos: Position) -> bool:
        """Returns True if the position is within the board boundaries."""
        return 0 <= pos.row < self.rows and 0 <= pos.col < self.cols

    def piece_at(self, pos: Position) -> Piece | None:
        """Returns the piece at the given position, or None if the cell is empty."""
        return self._cells.get(pos)

    def is_empty(self, pos: Position) -> bool:
        """Returns True if the given position has no piece on it."""
        return pos not in self._cells

    def add_piece(self, piece: Piece) -> None:
        """Places a piece on the board. Raises ValueError if the cell is already occupied."""
        if piece.cell in self._cells:
            raise ValueError(f"Cell {piece.cell} is already occupied")
        self._cells[piece.cell] = piece

    def remove_piece(self, pos: Position) -> Piece:
        """Removes and returns the piece at the given position. Raises ValueError if the cell is empty."""
        if pos not in self._cells:
            raise ValueError(f"No piece at {pos}")
        return self._cells.pop(pos)

    def move_piece(self, piece: Piece, destination: Position) -> None:
        """Moves a piece to the destination. Assumes validation and capture handling already occurred.
        Raises ValueError if the destination is occupied."""
        if destination in self._cells:
            raise ValueError(f"Cell {destination} is already occupied")
        del self._cells[piece.cell]
        piece.cell = destination
        self._cells[destination] = piece

    def all_pieces(self) -> list[Piece]:
        """Returns all pieces currently on the board."""
        return list(self._cells.values())
