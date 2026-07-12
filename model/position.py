from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def __post_init__(self):
        if self.row < 0 or self.col < 0:
            raise ValueError(f"Position out of bounds: ({self.row}, {self.col})")

    def __repr__(self):
        return f"({self.row}, {self.col})"
