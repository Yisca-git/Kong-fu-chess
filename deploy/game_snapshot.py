from dataclasses import dataclass
from piece import Piece


@dataclass(frozen=True)
class PieceSnapshot:
    id:    str
    color: str
    kind:  str
    row:   int
    col:   int


@dataclass(frozen=True)
class GameSnapshot:
    pieces:    tuple
    game_over: bool
    rows:      int
    cols:      int

    @staticmethod
    def from_pieces(pieces, game_over, rows, cols):
        """Creates a read-only snapshot from the current list of pieces."""
        snapshots = tuple(
            PieceSnapshot(p.id, p.color.value, p.kind.value, p.cell.row, p.cell.col)
            for p in pieces
        )
        return GameSnapshot(snapshots, game_over, rows, cols)
