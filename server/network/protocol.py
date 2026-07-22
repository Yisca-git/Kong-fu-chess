"""Wire protocol helpers: encode GameSnapshot → JSON, decode command string → (src, dst).

Command format:
  Move: <color><kind><src_col><src_row><dst_col><dst_row>  e.g. "WQe2e4"
  Jump: <color><kind><col><row>                            e.g. "WKe1"
"""
from __future__ import annotations
import json
from engine.game_snapshot import GameSnapshot
from engine.move_log import COL_LETTERS
from engine.setup import BOARD_ROWS

_COL_LETTERS = COL_LETTERS.lower()


def encode_snapshot(snap: GameSnapshot, force_game_over: bool = False,
                    winner: str | None = None) -> str:
    return json.dumps({
        "pieces": [
            {
                "id": p.id, "color": p.color, "kind": p.kind,
                "row": p.row, "col": p.col, "state": p.state,
                "mp": p.motion_progress,
                "dr": p.dest_row, "dc": p.dest_col,
                "cp": p.cooldown_progress,
            }
            for p in snap.pieces
        ],
        "game_over":   force_game_over or snap.game_over,
        "rows":        snap.rows,
        "cols":        snap.cols,
        "white_score": snap.white_score,
        "black_score": snap.black_score,
        "winner":      winner or snap.winner,
        "white_name":  snap.white_name,
        "black_name":  snap.black_name,
        "move_log": [
            {"color": e.color, "notation": e.notation, "time_ms": e.time_ms}
            for e in snap.move_log
        ],
        "rejection_reason": snap.rejection_reason,
    })


def _col(letter: str) -> int:
    return _COL_LETTERS.index(letter.lower())


def _row(digit: str) -> int:
    return BOARD_ROWS - int(digit)


def decode_command(cmd: str) -> tuple[str, tuple[int, int], tuple[int, int] | None]:
    """Returns (color, src, dst_or_None).  dst is None for jump commands.

    Move: W/B + kind + src_col + src_row + dst_col + dst_row  → body len 5  e.g. "WQe2e4"
    Jump: W/B + kind + col + row                              → body len 3  e.g. "WKe1"
    """
    color = "w" if cmd[0].upper() == "W" else "b"
    body  = cmd[1:]   # strip color prefix: kind + coords
    src   = (_row(body[2]), _col(body[1]))
    if len(body) == 3:   # jump
        return color, src, None
    dst = (_row(body[4]), _col(body[3]))
    return color, src, dst
