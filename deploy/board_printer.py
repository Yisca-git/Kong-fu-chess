from game_snapshot import GameSnapshot

EMPTY_CELL = '.'


def print_board(snapshot: GameSnapshot) -> None:
    """Prints the logical board state from a GameSnapshot to stdout."""
    grid = [[EMPTY_CELL] * snapshot.cols for _ in range(snapshot.rows)]

    for piece in snapshot.pieces:
        grid[piece.row][piece.col] = f"{piece.color}{piece.kind}"

    for row in grid:
        print(' '.join(row))
