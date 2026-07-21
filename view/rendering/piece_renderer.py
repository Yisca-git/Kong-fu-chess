from __future__ import annotations
from typing import TYPE_CHECKING
from view.img import Img
from view.sprites.sprite_library import SpriteLibrary
from view.sprites.sprite_state import AnimatedSprite
from model.piece import PieceState

if TYPE_CHECKING:
    from engine.game_snapshot import GameSnapshot, PieceSnapshot


class PieceRenderer:
    """Composites piece sprites onto a frame using AnimatedSprite (State Pattern).
    Handles motion_progress interpolation and cooldown bars.
    Rest transitions (short_rest/long_rest) are handled inside AnimatedSprite.
    """

    def __init__(self, library: SpriteLibrary) -> None:
        self._library = library
        self._sprites: dict[str, AnimatedSprite] = {}  # piece_id -> AnimatedSprite

    def draw(self, frame: Img, snapshot: GameSnapshot, dt_ms: int) -> None:
        cell = self._library.cell_size
        for piece in snapshot.pieces:
            sprite = self._animated_sprite_for(piece, dt_ms)
            x, y   = self._pixel_pos(piece, cell)
            sprite.draw_on(frame, x, y)
            if piece.cooldown_progress > 0.0:
                self._draw_cooldown(frame, x, y, piece.cooldown_progress, cell)

    def _animated_sprite_for(self, piece: PieceSnapshot, dt_ms: int) -> Img:
        existing = self._sprites.get(piece.id)
        if existing is None or existing.kind != piece.kind:
            self._sprites[piece.id] = AnimatedSprite(
                self._library, piece.color, piece.kind, piece.state
            )
        animated = self._sprites[piece.id]
        animated.update(dt_ms, piece.state)
        return animated.current_frame

    def _pixel_pos(self, piece: PieceSnapshot, cell: int) -> tuple[int, int]:
        if piece.state == PieceState.MOVING.value and piece.dest_row is not None and piece.motion_progress < 1.0:
            t = piece.motion_progress
            x = int((piece.col + t * (piece.dest_col - piece.col)) * cell)
            y = int((piece.row + t * (piece.dest_row - piece.row)) * cell)
            return x, y
        return piece.col * cell, piece.row * cell

    def _draw_cooldown(self, frame: Img, x: int, y: int, progress: float, cell: int) -> None:
        bar_h = int(cell * progress)
        frame.draw_rect_filled(x, y, cell, bar_h, color=(0, 215, 255), alpha=0.45)
