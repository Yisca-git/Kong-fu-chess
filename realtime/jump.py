from dataclasses import dataclass
from model.piece import Piece
from model.position import Position

JUMP_DURATION = 1000


@dataclass
class Jump:
    piece:      Piece
    cell:       Position
    start_time: int
    land_time:  int = 0

    def __post_init__(self):
        self.land_time = self.start_time + JUMP_DURATION
