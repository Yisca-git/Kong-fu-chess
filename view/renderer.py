from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from engine.game_snapshot import GameSnapshot
    from view.image_view import ImageView


class Renderer:
    """Draws the current game state to the screen.

    Placeholder — to be filled in once the graphics design files are available.
    Per the layering rules in ARCHITECTURE.md: the Renderer may only read from a
    GameSnapshot (read-only DTO) — it must never touch Board, GameEngine internals,
    RuleEngine, or RealTimeArbiter directly."""

    def __init__(self, image_view: ImageView):
        self._image_view = image_view

    def render(self, snapshot: GameSnapshot) -> None:
        """Draws the given snapshot. Not yet implemented."""
        raise NotImplementedError
