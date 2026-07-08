from dataclasses import dataclass
from typing import Callable
from config import MOVE_DURATION, EMPTY, WHITE


@dataclass
class PieceType:
    symbol: str
    move_duration: int
    can_move: Callable


def _pawn_can_move(dr, dc, context):
    color       = context['color']
    target      = context['target']
    is_at_start = context['is_at_start']
    path_clear  = context['path_clear']
    direction   = -1 if color == WHITE else 1

    if dc == 0 and dr == direction:
        return target == EMPTY
    if dc == 0 and is_at_start and dr == 2 * direction:
        return target == EMPTY and path_clear
    if abs(dc) == 1 and dr == direction:
        return target != EMPTY
    return False


PIECE_TYPES = {
    'K': PieceType('K', MOVE_DURATION, lambda dr, dc, _: abs(dr) <= 1 and abs(dc) <= 1),
    'N': PieceType('N', MOVE_DURATION, lambda dr, dc, _: (abs(dr) == 1 and abs(dc) == 2) or (abs(dr) == 2 and abs(dc) == 1)),
    'R': PieceType('R', MOVE_DURATION, lambda dr, dc, ctx: (dr == 0 or dc == 0) and ctx['path_clear']),
    'B': PieceType('B', MOVE_DURATION, lambda dr, dc, ctx: (abs(dr) == abs(dc)) and ctx['path_clear']),
    'Q': PieceType('Q', MOVE_DURATION, lambda dr, dc, ctx: (dr == 0 or dc == 0 or abs(dr) == abs(dc)) and ctx['path_clear']),
    'P': PieceType('P', MOVE_DURATION, _pawn_can_move),
}
