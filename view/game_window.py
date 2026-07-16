from __future__ import annotations
import time
import cv2
from engine.game_engine import GameEngine
from input.controller import Controller
from view.renderer import Renderer
from view.config import PANEL_W, TICK_MS, WINDOW_NAME


class GameWindow:
    """Owns the OpenCV window, mouse input, and the main render loop.

    The only file in the project (besides the vendored view/img.py) that imports cv2
    directly — strictly for window lifecycle, mouse-callback plumbing, and the non-blocking
    render loop that Img itself doesn't provide (Img.show() is blocking). All actual drawing
    still goes through Img, via Renderer/SpriteLoader."""

    def __init__(self, engine: GameEngine, controller: Controller, renderer: Renderer):
        self._engine     = engine
        self._controller = controller
        self._renderer   = renderer

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        """cv2 mouse callback: translates window coords to board coords by subtracting PANEL_W."""
        board_x = x - PANEL_W
        self._engine.set_cursor(board_x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.handle_click(board_x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._controller.handle_jump(board_x, y)

    def run(self) -> None:
        """Runs the main loop until the window is closed, or Esc/q is pressed."""
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        start_ms = time.monotonic() * 1000
        last_ms  = start_ms
        try:
            while True:
                now_ms  = time.monotonic() * 1000
                elapsed = int(now_ms - last_ms)
                last_ms = now_ms

                if elapsed > 0:
                    self._engine.advance_time(elapsed)

                snapshot = self._engine.snapshot()
                canvas   = self._renderer.render(snapshot, int(now_ms - start_ms))
                cv2.imshow(WINDOW_NAME, canvas.raw())
                if snapshot.rejection_reason is not None:
                    self._engine.set_rejection(None)

                key = cv2.waitKey(TICK_MS) & 0xFF
                if key in (27, ord('q')):  # Esc or q
                    break
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cv2.destroyAllWindows()
