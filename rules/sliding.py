from model.board import Board
from model.piece import Piece
from model.position import Position


def slide(board: Board, piece: Piece, directions: list[tuple[int, int]]) -> set[Position]:
    """Slides in each direction until hitting a boundary or a blocking piece."""
    destinations = set()
    for dr, dc in directions:
        r, c = piece.cell.row + dr, piece.cell.col + dc
        while True:
            pos = Position(r, c)
            if not board.in_bounds(pos):
                break
            occupant = board.piece_at(pos)
            if occupant is not None:
                if occupant.color != piece.color:
                    destinations.add(pos)
                break
            destinations.add(pos)
            r += dr
            c += dc
    return destinations
