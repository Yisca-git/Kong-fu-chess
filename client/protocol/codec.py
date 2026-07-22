"""Encode/decode wire messages between client and server."""
from __future__ import annotations
from engine.game_snapshot import GameSnapshot, PieceSnapshot
from engine.move_log import MoveEntry

_COL_LETTERS = "abcdefgh"


def parse_snapshot(data: dict) -> GameSnapshot:
    pieces = tuple(
        PieceSnapshot(
            id=p["id"], color=p["color"], kind=p["kind"],
            row=p["row"], col=p["col"], state=p["state"],
            motion_progress=p["mp"],
            dest_row=p["dr"], dest_col=p["dc"],
            cooldown_progress=p["cp"],
        )
        for p in data["pieces"]
    )
    move_log = tuple(
        MoveEntry(e["color"], e["notation"], e["time_ms"])
        for e in data.get("move_log", [])
    )
    return GameSnapshot(
        pieces=pieces,
        game_over=data["game_over"],
        rows=data["rows"],
        cols=data["cols"],
        white_score=data["white_score"],
        black_score=data["black_score"],
        winner=data.get("winner"),
        white_name=data.get("white_name", "White"),
        black_name=data.get("black_name", "Black"),
        move_log=move_log,
        rejection_reason=data.get("rejection_reason"),
    )


def encode_move(color: str, kind: str, src_row: int, src_col: int,
                dst_row: int, dst_col: int) -> str:
    c  = "W" if color == "w" else "B"
    return f"{c}{kind}{_COL_LETTERS[src_col]}{8 - src_row}{_COL_LETTERS[dst_col]}{8 - dst_row}"


def encode_jump(color: str, kind: str, row: int, col: int) -> str:
    c = "W" if color == "w" else "B"
    return f"{c}{kind}{_COL_LETTERS[col]}{8 - row}"
