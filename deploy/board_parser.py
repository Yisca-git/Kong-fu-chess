from board import Board
from piece import Piece, Color, Kind, PieceState
from position import Position

_COLOR_MAP = {c.value: c for c in Color}
_KIND_MAP  = {k.value: k for k in Kind}

EMPTY_CELL = '.'


def validate(text):
    """Validates the board section. Prints ERROR and returns False if invalid."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    board_start = lines.index("Board:") + 1
    board_end   = lines.index("Commands:")
    raw_rows    = lines[board_start:board_end]

    cols = len(raw_rows[0].split())
    for row in raw_rows:
        if len(row.split()) != cols:
            print("ERROR ROW_WIDTH_MISMATCH")
            return False
    for row in raw_rows:
        for token in row.split():
            if token == EMPTY_CELL:
                continue
            if token[0] not in _COLOR_MAP or len(token) < 2 or token[1] not in _KIND_MAP:
                print("ERROR UNKNOWN_TOKEN")
                return False
    return True


def parse(text):
    """Parses a text board definition into a Board and a list of Piece objects."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    board_start = lines.index("Board:") + 1
    board_end   = lines.index("Commands:")
    raw_rows    = lines[board_start:board_end]

    cols = len(raw_rows[0].split())
    rows = len(raw_rows)
    board = Board(rows, cols)

    pieces = []
    counters = {}

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
