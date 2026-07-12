from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    row: int
    col: int

    def __repr__(self):
        return f"({self.row}, {self.col})"
