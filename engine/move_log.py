from __future__ import annotations
from dataclasses import dataclass

COL_LETTERS = "ABCDEFGH"


def to_notation(kind: str, src_row: int, src_col: int, dest_row: int, dest_col: int, capture: bool) -> str:
    """Returns notation: e.g. 'R A8→E8', 'P E2→E4', 'N G1→F3 X'"""
    def square(row, col):
        col_letter = COL_LETTERS[col] if col < len(COL_LETTERS) else str(col)
        return f"{col_letter}{8 - row}"
    capture_mark = " X" if capture else ""
    return f"{kind} {square(src_row, src_col)}→{square(dest_row, dest_col)}{capture_mark}"


@dataclass(frozen=True)
class MoveEntry:
    color:    str   # "w" or "b"
    notation: str
    time_ms:  int
