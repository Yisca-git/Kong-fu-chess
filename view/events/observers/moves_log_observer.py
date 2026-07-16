from __future__ import annotations
from dataclasses import dataclass
from engine.events import MoveResolvedEvent, JumpResolvedEvent
from engine.move_log import to_notation


@dataclass(frozen=True)
class LogEntry:
    color:    str
    notation: str
    time_ms:  int


class MovesLogObserver:
    """Subscribed once in app.py. Appends a LogEntry per side on every settlement."""

    def __init__(self) -> None:
        self.entries: list[LogEntry] = []

    def on_move_resolved(self, event: MoveResolvedEvent) -> None:
        self.entries.append(LogEntry(
            color=event.piece_color,
            notation=to_notation(event.piece_kind, event.src[0], event.src[1],
                                 event.dst[0], event.dst[1],
                                 event.captured_piece_kind is not None),
            time_ms=event.time_ms,
        ))

    def on_jump_resolved(self, event: JumpResolvedEvent) -> None:
        self.entries.append(LogEntry(
            color=event.piece_color,
            notation=to_notation(event.piece_kind, event.pos[0], event.pos[1],
                                 event.pos[0], event.pos[1],
                                 event.captured_piece_kind is not None),
            time_ms=event.time_ms,
        ))
