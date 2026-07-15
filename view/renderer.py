from __future__ import annotations
from typing import TYPE_CHECKING
from model.piece import Kind, Color
from view.img import Img
from view.sprite_loader import SpriteLoader, CELL_SIZE
from view.piece_animator import PieceAnimator
import numpy as np

if TYPE_CHECKING:
    from engine.game_snapshot import GameSnapshot, PieceSnapshot

PANEL_W      = 200
LOG_FONT     = 0.4
LOG_COLOR    = (220, 220, 220)
HEADER_COLOR = (255, 255, 100)
MAX_ENTRIES  = 20  # max rows visible per panel


class Renderer:
    """Draws the current game state to the screen.

    Per the layering rules in ARCHITECTURE.md: the Renderer may only read from a
    GameSnapshot (read-only DTO) — it must never touch Board, GameEngine internals,
    RuleEngine, or RealTimeArbiter directly."""

    def __init__(self, sprite_loader: SpriteLoader):
        self._sprites  = sprite_loader
        self._animator = PieceAnimator()

    def render(self, snapshot: GameSnapshot, now_ms: int) -> Img:
        """Composes board + pieces + move-log panels into one Img canvas."""
        board_canvas = self._render_board(snapshot, now_ms)
        full = self._compose_with_panels(board_canvas, snapshot)
        if snapshot.game_over:
            self._draw_game_over(full, snapshot)
        return full

    # ------------------------------------------------------------------ board

    def _render_board(self, snapshot: GameSnapshot, now_ms: int) -> Img:
        canvas = self._fresh_board_canvas(snapshot.rows, snapshot.cols)
        if snapshot.selected_row is not None:
            canvas.draw_rect(
                snapshot.selected_col * CELL_SIZE,
                snapshot.selected_row * CELL_SIZE,
                CELL_SIZE, CELL_SIZE,
            )
        for piece in snapshot.pieces:
            sprite = self._sprite_for(piece, now_ms)
            x, y   = self._piece_pixel_pos(piece)
            sprite.draw_on(canvas, x, y)
            if piece.cooldown_progress > 0.0:
                self._draw_cooldown(canvas, x, y, piece.cooldown_progress)
        return canvas

    # ------------------------------------------------------------------ panels

    def _compose_with_panels(self, board_canvas: Img, snapshot: GameSnapshot) -> Img:
        """Stitches [white panel | board | black panel] horizontally."""
        bh, bw = board_canvas.img.shape[:2]
        total_w = PANEL_W + bw + PANEL_W

        full = Img().new(total_w, bh, channels=board_canvas.img.shape[2])

        # board in the middle
        full.img[:, PANEL_W:PANEL_W + bw] = board_canvas.img

        white_entries = [e for e in snapshot.move_log if e.color == "w"]
        black_entries = [e for e in snapshot.move_log if e.color == "b"]

        self._draw_log_panel(full, white_entries, x_offset=0,           title="White")
        self._draw_log_panel(full, black_entries, x_offset=PANEL_W + bw, title="Black")

        # scores
        full.put_text(f"Score: {snapshot.white_score}", 5, bh - 10, 0.45, HEADER_COLOR)
        full.put_text(f"Score: {snapshot.black_score}", PANEL_W + bw + 5, bh - 10, 0.45, HEADER_COLOR)

        return full

    def _draw_game_over(self, canvas: Img, snapshot: GameSnapshot) -> None:
        winner_name = "White" if snapshot.winner == "w" else "Black" if snapshot.winner == "b" else "?"
        h, w = canvas.img.shape[:2]
        canvas.put_text(f"{winner_name} Wins!", w // 2 - 120, h // 2, 1.5, (0, 255, 0), thickness=3)

    def _draw_log_panel(self, canvas: Img, entries: list, x_offset: int, title: str) -> None:
        canvas.put_text(title, x_offset + 5, 20, 0.5, HEADER_COLOR, thickness=1)
        visible = entries[-MAX_ENTRIES:]
        for i, entry in enumerate(visible):
            secs = entry.time_ms // 1000
            text = f"{secs:>3}s {entry.notation}"
            canvas.put_text(text, x_offset + 5, 45 + i * 18, LOG_FONT, LOG_COLOR)

    # ------------------------------------------------------------------ helpers

    def _draw_cooldown(self, canvas: Img, x: int, y: int, progress: float) -> None:
        """Draws a yellow bar descending over the piece — full at progress=1.0, gone at 0.0."""
        bar_h = int(CELL_SIZE * progress)
        canvas.draw_rect_filled(x, y, CELL_SIZE, bar_h, color=(0, 215, 255), alpha=0.45)

    def _piece_pixel_pos(self, piece: PieceSnapshot) -> tuple[int, int]:
        """Returns the top-left pixel position for a piece, interpolated during motion."""
        if piece.state == "moving" and piece.dest_row is not None and piece.motion_progress < 1.0:
            t = piece.motion_progress
            x = int((piece.col + t * (piece.dest_col - piece.col)) * CELL_SIZE)
            y = int((piece.row + t * (piece.dest_row - piece.row)) * CELL_SIZE)
            return x, y
        return piece.col * CELL_SIZE, piece.row * CELL_SIZE

    def _sprite_for(self, piece: PieceSnapshot, now_ms: int) -> Img:
        """Picks the current animation frame to draw for a piece, based on its state."""
        kind          = Kind(piece.kind)
        color         = Color(piece.color)
        display_state = self._animator.update_display_state(piece.id, piece.state, now_ms)
        folder_state  = self._animator.folder_state_for(display_state)
        frames        = self._sprites.frames_for(kind, color, folder_state)
        index         = self._animator.frame_index(piece.id, display_state, now_ms, len(frames))
        return frames[index]

    def _fresh_board_canvas(self, rows: int, cols: int) -> Img:
        """Returns a new Img with a copy of the cached board background."""
        board  = self._sprites.board_image(rows, cols)
        canvas = Img()
        canvas.img = board.img.copy()
        return canvas
