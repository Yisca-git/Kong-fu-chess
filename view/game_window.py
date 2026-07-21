from __future__ import annotations
import time
import cv2
from engine.game_engine import GameEngine
from input.controller import Controller
from view.renderer import Renderer
from view.config import PANEL_W, TICK_MS, WINDOW_NAME, CELL_SIZE

_MIN_CELL = 50
_MAX_CELL = 160


class GameWindow:
    def __init__(self, engine: GameEngine, controller: Controller, renderer: Renderer):
        self._engine     = engine
        self._controller = controller
        self._renderer   = renderer
        self._cell_size  = CELL_SIZE
        snap = engine.snapshot()
        self._rows = snap.rows
        self._cols = snap.cols

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        board_x = x - PANEL_W
        self._engine.set_cursor(board_x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            self._controller.handle_click(board_x, y)
        elif event == cv2.EVENT_RBUTTONDOWN:
            self._controller.handle_jump(board_x, y)

    def _update_cell_size(self, win_w: int, win_h: int) -> None:
        board_w = win_w - 2 * PANEL_W
        cell    = max(_MIN_CELL, min(_MAX_CELL, min(board_w // self._cols, win_h // self._rows)))
        if cell != self._cell_size:
            self._cell_size = cell
            self._controller.set_cell_size(cell)
            self._renderer.set_cell_size(cell)

    def run(self) -> None:
        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)
        cv2.resizeWindow(WINDOW_NAME,
                         2 * PANEL_W + self._cols * self._cell_size,
                         self._rows * self._cell_size)

        start_ms = time.monotonic() * 1000
        last_ms  = start_ms
        try:
            while True:
                now_ms  = time.monotonic() * 1000
                elapsed = int(now_ms - last_ms)
                last_ms = now_ms

                if elapsed > 0:
                    self._engine.advance_time(elapsed)

                rect = cv2.getWindowImageRect(WINDOW_NAME)
                if rect[2] > 0 and rect[3] > 0:
                    self._update_cell_size(rect[2], rect[3])

                snapshot = self._engine.snapshot()
                canvas   = self._renderer.render(snapshot, int(now_ms - start_ms))
                cv2.imshow(WINDOW_NAME, canvas.raw())
                if snapshot.rejection_reason is not None:
                    self._engine.set_rejection(None)

                key = cv2.waitKey(TICK_MS) & 0xFF
                if key in (27, ord('q')):
                    break
                if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    break
        finally:
            cv2.destroyAllWindows()
