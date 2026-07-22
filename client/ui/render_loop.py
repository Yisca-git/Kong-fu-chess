"""Shared OpenCV render loop for network clients."""
from __future__ import annotations
import time
import threading
import cv2

from engine.game_snapshot import GameSnapshot
from view.renderer import Renderer
from view.sprites.sprite_library import SpriteLibrary
from view.config import TICK_MS, WINDOW_NAME, CELL_SIZE


class RenderLoop:
    """Base render loop: opens a cv2 window and renders snapshots until game over or quit."""

    def __init__(self, window_name: str = WINDOW_NAME) -> None:
        self._renderer    = Renderer(SpriteLibrary(cell_size=CELL_SIZE))
        self._snapshot:   GameSnapshot | None = None
        self._user_closed = False
        self._window_name = window_name

    def _ready_event(self) -> threading.Event:
        raise NotImplementedError

    def _start_ws_thread(self) -> None:
        raise NotImplementedError

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        pass  # override in subclasses that need input

    def _on_tick(self, snap: GameSnapshot) -> None:
        pass  # override in subclasses that need per-frame hooks (e.g. sound)

    def _wait_for_ready(self, timeout: float) -> bool:
        return self._ready_event().wait(timeout=timeout)

    def _run_loop(self) -> None:
        cv2.namedWindow(self._window_name, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(self._window_name, self._on_mouse)
        start_ms = time.monotonic() * 1000
        while True:
            now_ms = int(time.monotonic() * 1000 - start_ms)
            snap   = self._snapshot
            if snap is not None:
                self._on_tick(snap)
                canvas = self._renderer.render(snap, now_ms)
                cv2.imshow(self._window_name, canvas.raw())
                if snap.game_over:
                    cv2.waitKey(2000)
                    break
            key = cv2.waitKey(TICK_MS) & 0xFF
            if key in (27, ord('q')):
                self._user_closed = True
                break
            if cv2.getWindowProperty(self._window_name, cv2.WND_PROP_VISIBLE) < 1:
                self._user_closed = True
                break
        cv2.destroyAllWindows()
        self._on_window_closed()

    def _on_window_closed(self) -> None:
        pass  # override in subclasses
