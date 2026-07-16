from __future__ import annotations
from typing import TYPE_CHECKING
from view.img import Img
from view.config import PANEL_W, LOG_FONT, LOG_COLOR, HEADER_COLOR, MAX_LOG_ENTRIES
from input.board_mapper import CELL_SIZE
from model.piece import Color

if TYPE_CHECKING:
    from engine.game_snapshot import GameSnapshot

_REJECTION_LABELS: dict[str, str] = {
    "piece_already_moving":   "Already moving!",
    "piece_on_cooldown":      "On cooldown!",
    "piece_already_airborne": "Already airborne!",
    "illegal_piece_move":     "Illegal move!",
    "friendly_destination":   "Friendly piece!",
    "friendly_airborne_destination": "Friendly airborne!",
    "empty_source":           "No piece there!",
    "outside_board":          "Outside board!",
    "game_over":              "Game over!",
}


class OverlayRenderer:
    """Draws everything that isn't the board background or a piece sprite:
    selection highlight, side panels (moves log + score), and game-over banner."""

    def draw_selection(self, frame: Img, snapshot: GameSnapshot) -> None:
        if snapshot.selected_row is not None:
            frame.draw_rect(
                snapshot.selected_col * CELL_SIZE,
                snapshot.selected_row * CELL_SIZE,
                CELL_SIZE, CELL_SIZE,
            )

    def compose_panels(self, board_canvas: Img, snapshot: GameSnapshot) -> Img:
        """Wraps the board canvas with left (White) and right (Black) side panels."""
        bh, bw  = board_canvas.height(), board_canvas.width()
        total_w = PANEL_W + bw + PANEL_W
        full    = Img().new(total_w, bh, channels=board_canvas.channels())
        full.paste(board_canvas, PANEL_W, 0, bw)

        white_entries = [e for e in snapshot.move_log if e.color == Color.WHITE.value]
        black_entries = [e for e in snapshot.move_log if e.color == Color.BLACK.value]
        self._draw_log_panel(full, white_entries, x_offset=0,
                             name=snapshot.white_name, score=snapshot.white_score)
        self._draw_log_panel(full, black_entries, x_offset=PANEL_W + bw,
                             name=snapshot.black_name, score=snapshot.black_score)
        return full

    def draw_game_over(self, canvas: Img, snapshot: GameSnapshot) -> None:
        winner = "White" if snapshot.winner == Color.WHITE.value else "Black" if snapshot.winner == Color.BLACK.value else "?"
        h, w   = canvas.height(), canvas.width()
        canvas.put_text(f"{winner} Wins!", w // 2 - 120, h // 2, 1.5, (0, 255, 0), thickness=3)

    def draw_rejection(self, canvas: Img, snapshot: GameSnapshot) -> None:
        """Draws a one-frame rejection reason tooltip in the centre of the board area."""
        if snapshot.rejection_reason is None:
            return
        label = _REJECTION_LABELS.get(snapshot.rejection_reason, snapshot.rejection_reason)
        h, w  = canvas.height(), canvas.width()
        cx    = PANEL_W + (w - 2 * PANEL_W) // 2
        canvas.draw_rect_filled(cx - 110, h // 2 - 22, 220, 34, color=(30, 30, 30), alpha=0.75)
        canvas.put_text(label, cx - 105, h // 2, 0.65, (0, 80, 255), thickness=2)

    # ------------------------------------------------------------------ private

    def _draw_log_panel(self, canvas: Img, entries: list, x_offset: int,
                        name: str, score: int) -> None:
        canvas.put_text(name,            x_offset + 5, 20, 0.55, HEADER_COLOR, thickness=2)
        canvas.put_text(f"Score: {score}", x_offset + 5, 42, 0.45, HEADER_COLOR, thickness=1)
        for i, entry in enumerate(entries[-MAX_LOG_ENTRIES:]):
            secs = entry.time_ms // 1000
            canvas.put_text(f"{secs:>3}s {entry.notation}", x_offset + 5, 65 + i * 18,
                            LOG_FONT, LOG_COLOR)
