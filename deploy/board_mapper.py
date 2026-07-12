from position import Position

CELL_SIZE = 100


def pixel_to_position(x: int, y: int) -> Position:
    """Converts pixel coordinates to a board position using a fixed cell size."""
    return Position(row=y // CELL_SIZE, col=x // CELL_SIZE)
