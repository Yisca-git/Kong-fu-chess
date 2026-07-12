from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position

_COLOR_MAP = {c.value: c for c in Color}
_KIND_MAP  = {k.value: k for k in Kind}

EMPTY_CELL = '.'


def parse(text: str) -> tuple[Board, list[Piece]]:
    """Parses a text board definition into a Board and a list of Piece objects."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    board_start = lines.index("Board:") + 1
    board_end   = lines.index("Commands:")
    raw_rows    = lines[board_start:board_end]

    cols = len(raw_rows[0].split())
    rows = len(raw_rows)
    board = Board(rows, cols)

    pieces: list[Piece] = []
    counters: dict[str, int] = {}

    for r, row in enumerate(raw_rows):
        for c, token in enumerate(row.split()):
            if token == EMPTY_CELL:
                continue
            color = _COLOR_MAP[token[0]]
            kind  = _KIND_MAP[token[1]]
            key   = token
            counters[key] = counters.get(key, 0) + 1
            piece = Piece(
                id    = f"{token}{counters[key]}",
                color = color,
                kind  = kind,
                cell  = Position(r, c),
                state = PieceState.IDLE,
            )
            board.add_piece(piece)
            pieces.append(piece)

    return board, pieces
