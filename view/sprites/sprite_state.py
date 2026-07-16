from __future__ import annotations
import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from model.piece import PieceState

if TYPE_CHECKING:
    from view.img import Img
    from view.sprites.sprite_library import SpriteLibrary


class AnimState(str, Enum):
    """Animation states that exist only in the view layer (not in the engine)."""
    SHORT_REST = "short_rest"
    LONG_REST  = "long_rest"


@dataclass(frozen=True)
class StateConfig:
    """Parsed from a state folder's config.json. Immutable."""
    name: str
    frames_per_sec: float
    is_loop: bool
    next_state_when_finished: str | None

    @staticmethod
    def from_json(path: Path, state_name: str) -> "StateConfig":
        data = json.loads(path.read_text())
        graphics = data["graphics"]
        physics  = data["physics"]
        return StateConfig(
            name=state_name,
            frames_per_sec=float(graphics["frames_per_sec"]),
            is_loop=bool(graphics["is_loop"]),
            next_state_when_finished=physics.get("next_state_when_finished"),
        )


class SpriteState:
    """One playable animation state. Owns its frame list and playback clock.
    Knows nothing about other states except the name to hand control to when done."""

    def __init__(self, config: StateConfig, frames: list["Img"]) -> None:
        if not frames:
            raise ValueError(f"SpriteState '{config.name}' has no frames")
        self._config    = config
        self._frames    = frames
        self._elapsed_ms = 0.0

    @property
    def name(self) -> str:
        return self._config.name

    def reset(self) -> None:
        self._elapsed_ms = 0.0

    def advance(self, dt_ms: float) -> None:
        self._elapsed_ms += dt_ms

    @property
    def current_frame(self) -> "Img":
        idx = int(self._elapsed_ms * self._config.frames_per_sec / 1000.0)
        if self._config.is_loop:
            idx %= len(self._frames)
        else:
            idx = min(idx, len(self._frames) - 1)
        return self._frames[idx]

    @property
    def is_finished(self) -> bool:
        if self._config.is_loop:
            return False
        total_ms = len(self._frames) * 1000.0 / self._config.frames_per_sec
        return self._elapsed_ms >= total_ms

    @property
    def next_state_when_finished(self) -> str | None:
        return self._config.next_state_when_finished


# engine states that play a rest animation before returning to idle
_REST_AFTER: dict[str, str] = {
    PieceState.MOVING.value:   AnimState.SHORT_REST.value,
    PieceState.AIRBORNE.value: AnimState.LONG_REST.value,
}


class AnimatedSprite:
    """Per-piece driver. Holds one current SpriteState and asks SpriteLibrary
    (Strategy) for replacements — never branches on state names itself.

    When the engine transitions to 'idle' after 'moving' or 'airborne',
    inserts a rest animation (short_rest/long_rest) before idle — driven by
    _REST_AFTER here and next_state_when_finished in config.json, not by
    if/else chains on state names.
    """

    def __init__(self, library: "SpriteLibrary", color: str, kind: str,
                 initial_state: str = PieceState.IDLE.value) -> None:
        self._library       = library
        self._color         = color
        self._kind          = kind
        self._engine_state  = initial_state
        self._current       = library.get_state(color, kind, initial_state)
        self._current.reset()

    @property
    def kind(self) -> str:
        return self._kind

    def update(self, dt_ms: float, engine_state: str) -> None:
        """Advance animation by dt_ms. Handles engine state changes and rest transitions."""
        if engine_state != self._engine_state:
            prev = self._engine_state
            self._engine_state = engine_state
            rest = _REST_AFTER.get(prev) if engine_state == PieceState.IDLE.value else None
            self._transition_to(rest if rest else engine_state)
            return
        self._current.advance(dt_ms)
        if self._current.is_finished and self._current.next_state_when_finished:
            self._transition_to(self._current.next_state_when_finished)

    def _transition_to(self, state_name: str) -> None:
        self._current = self._library.get_state(self._color, self._kind, state_name)
        self._current.reset()

    @property
    def current_frame(self) -> "Img":
        return self._current.current_frame
