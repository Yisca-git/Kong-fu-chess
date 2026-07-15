from dataclasses import dataclass
from model.piece import Piece
from engine.move_log import MoveEntry


@dataclass(frozen=True)
class PieceSnapshot:
    id:               str
    color:            str
    kind:             str
    row:              int
    col:              int
    state:            str   = "idle"
    motion_progress:  float = 1.0
    dest_row:         int | None = None
    dest_col:         int | None = None
    cooldown_progress: float = 0.0  # 1.0=just started cooldown, 0.0=ready


@dataclass(frozen=True)
class GameSnapshot:
    pieces:       tuple[PieceSnapshot, ...]
    game_over:    bool
    rows:         int
    cols:         int
    white_score:  int = 0
    black_score:  int = 0
    selected_row: int | None = None
    selected_col: int | None = None
    move_log:     tuple[MoveEntry, ...] = ()
    winner:       str | None = None  # "w" or "b", set when game_over is True

    @staticmethod
    def from_pieces(pieces: list[Piece], game_over: bool, rows: int, cols: int,
                     white_score: int = 0, black_score: int = 0,
                     selected_row: int | None = None, selected_col: int | None = None,
                     motion_progress_for=None, motion_destination_for=None,
                     move_log: list[MoveEntry] | None = None,
                     cooldown_progress_for=None,
                     winner: str | None = None) -> 'GameSnapshot':
        """Creates a read-only snapshot from the current list of pieces."""
        def _progress(p: Piece) -> float:
            return motion_progress_for(p) if motion_progress_for else 1.0
        def _dest(p: Piece):
            return motion_destination_for(p) if motion_destination_for else None
        def _cooldown(p: Piece) -> float:
            return cooldown_progress_for(p) if cooldown_progress_for else 0.0
        snapshots = tuple(
            PieceSnapshot(
                p.id, p.color.value, p.kind.value, p.cell.row, p.cell.col, p.state.value,
                _progress(p),
                _dest(p).row if _dest(p) else None,
                _dest(p).col if _dest(p) else None,
                _cooldown(p),
            )
            for p in pieces
        )
        return GameSnapshot(snapshots, game_over, rows, cols, white_score, black_score,
                            selected_row, selected_col, tuple(move_log) if move_log else (),
                            winner)
