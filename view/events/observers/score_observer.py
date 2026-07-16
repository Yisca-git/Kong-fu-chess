from __future__ import annotations
from engine.events import MoveResolvedEvent, JumpResolvedEvent
from engine.score_keeper import PIECE_VALUES


class ScoreObserver:
    """Subscribed once in app.py. Tracks captured-piece score per side.
    Pure side-effect object — no engine or renderer reference."""

    def __init__(self) -> None:
        self.score: dict[str, int] = {"w": 0, "b": 0}

    def on_move_resolved(self, event: MoveResolvedEvent) -> None:
        self._apply(event.captured_piece_kind, event.piece_color)

    def on_jump_resolved(self, event: JumpResolvedEvent) -> None:
        self._apply(event.captured_piece_kind, event.piece_color)

    def _apply(self, captured_kind: str | None, capturing_color: str) -> None:
        if captured_kind is not None:
            from model.piece import Kind
            kind_enum = next((k for k in Kind if k.value == captured_kind), None)
            if kind_enum is not None:
                self.score[capturing_color] += PIECE_VALUES.get(kind_enum, 0)
