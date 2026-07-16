from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class MoveResolvedEvent:
    src:                  tuple[int, int]
    dst:                  tuple[int, int]
    piece_kind:           str
    piece_color:          str
    captured_piece_kind:  str | None  # None if no capture
    time_ms:              int


@dataclass(frozen=True)
class JumpResolvedEvent:
    pos:                  tuple[int, int]
    piece_kind:           str
    piece_color:          str
    captured_piece_kind:  str | None
    time_ms:              int
