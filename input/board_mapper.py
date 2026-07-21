from model.position import Position


def pixel_to_position(x: int, y: int, cell_size: int) -> Position:
    """Converts pixel coordinates to a board position."""
    return Position(row=y // cell_size, col=x // cell_size)
