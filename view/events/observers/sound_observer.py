"""Sound observer — plays audio cues on game events.

Uses winsound on Windows (stdlib, no extra deps) with a thread-pool so audio
never blocks the render loop.  Falls back to a no-op on non-Windows platforms.
"""
from __future__ import annotations
import concurrent.futures
import sys

from view.events.events import MoveResolvedEvent, JumpResolvedEvent
from paths import ASSETS_ROOT

_SOUNDS_DIR = ASSETS_ROOT / "sounds"

_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="sound")


def _play(filename: str) -> None:
    path = _SOUNDS_DIR / filename
    if not path.exists():
        return
    try:
        if sys.platform == "win32":
            import winsound
            winsound.PlaySound(str(path), winsound.SND_FILENAME)
    except Exception:
        pass


class SoundObserver:
    def play_sound(self, filename: str) -> None:
        _executor.submit(_play, filename)

    def on_move_resolved(self, event: MoveResolvedEvent) -> None:
        self.play_sound("capture.wav" if event.captured_piece_kind else "move.wav")

    def on_jump_resolved(self, event: JumpResolvedEvent) -> None:
        self.play_sound("capture.wav" if event.captured_piece_kind else "jump.wav")
