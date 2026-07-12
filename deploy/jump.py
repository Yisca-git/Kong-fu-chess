from dataclasses import dataclass
from piece import Piece
from position import Position

JUMP_DURATION    = 1000
JUMP_COOLDOWN_MS = 500


@dataclass
class Jump:
    piece:      Piece
    cell:       Position
    start_time: int
    land_time:  int = 0
    ready_time: int = 0

    def __post_init__(self):
        self.land_time  = self.start_time + JUMP_DURATION
        self.ready_time = self.land_time  + JUMP_COOLDOWN_MS
