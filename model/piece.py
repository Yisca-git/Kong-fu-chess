from dataclasses import dataclass
from enum import Enum
from model.position import Position


class Color(Enum):
    WHITE = 'w'
    BLACK = 'b'


class Kind(Enum):
    KING   = 'K'
    QUEEN  = 'Q'
    ROOK   = 'R'
    BISHOP = 'B'
    KNIGHT = 'N'
    PAWN   = 'P'


class PieceState(Enum):
    IDLE     = 'idle'
    MOVING   = 'moving'
    CAPTURED = 'captured'


@dataclass
class Piece:
    id:    str
    color: Color
    kind:  Kind
    cell:  Position
    state: PieceState = PieceState.IDLE
