from dataclasses import dataclass, field
from model.piece import Piece
from model.position import Position

MS_PER_STEP = 1000


@dataclass
class Motion:
    piece:        Piece
    origin:       Position
    destination:  Position
    start_time:   int
    arrival_time: int = field(init=False)

    def __post_init__(self):
        steps = max(
            abs(self.destination.row - self.origin.row),
            abs(self.destination.col - self.origin.col),
        )
        self.arrival_time = self.start_time + steps * MS_PER_STEP
