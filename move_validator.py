from config import EMPTY
from pieces import PIECE_TYPES


def is_legal_move(piece_symbol, from_row, from_col, to_row, to_col, board):
    dr = to_row - from_row
    dc = to_col - from_col

    if to_row == from_row and to_col == from_col:
        return False

    current = board.get(from_row, from_col)
    target  = board.get(to_row, to_col)

    if current == EMPTY:
        return False
    if target != EMPTY and target[0] == current[0]:
        return False

    piece_type = PIECE_TYPES.get(piece_symbol)
    if piece_type is None:
        return False

    color       = current[0]
    is_at_start = (from_row == board.rows - 2) if color == 'w' else (from_row == 1)

    context = {
        'color':       color,
        'target':      target,
        'is_at_start': is_at_start,
        'path_clear':  board.is_path_clear(from_row, from_col, to_row, to_col),
    }

    return piece_type.can_move(to_row - from_row, to_col - from_col, context)
