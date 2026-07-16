from __future__ import annotations
from typing import TYPE_CHECKING
from view.img import Img
from view.sprites.sprite_library import SpriteLibrary
from view.rendering.board_renderer import BoardRenderer
from view.rendering.piece_renderer import PieceRenderer
from view.rendering.overlay_renderer import OverlayRenderer
from view.rendering.board_view import BoardView
from view.config import PANEL_W

if TYPE_CHECKING:
    from engine.game_snapshot import GameSnapshot


class Renderer:
    """Public entry point for rendering. Constructs and owns the BoardView collaborators."""

    def __init__(self, library: SpriteLibrary) -> None:
        self._view    = BoardView(
            board_renderer   = BoardRenderer(library),
            piece_renderer   = PieceRenderer(library),
            overlay_renderer = OverlayRenderer(),
        )
        self._last_ms = 0

    def render(self, snapshot: GameSnapshot, now_ms: int) -> Img:
        dt_ms         = max(0, now_ms - self._last_ms)
        self._last_ms = now_ms
        return self._view.render(snapshot, dt_ms)
