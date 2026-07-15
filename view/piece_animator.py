from __future__ import annotations

FRAME_DURATION_MS = 150
REST_DURATION_MS  = 750  # how long short_rest plays before returning to idle

_STATE_FOLDER: dict[str, str] = {
    "idle":       "idle",
    "moving":     "move",
    "airborne":   "jump",
    "short_rest": "short_rest",
    "long_rest":  "long_rest",
}

# After these engine states end, play a rest animation before idle
_REST_AFTER: dict[str, str] = {
    "moving":   "short_rest",
    "airborne": "long_rest",
}


class PieceAnimator:
    """Picks which sprite frame to show for a piece, based on its current state and how
    long it's been in that state. Pure view-state, keyed by piece id — knows nothing about
    Board, GameEngine, or RealTimeArbiter."""

    def __init__(self):
        # piece_id -> (display_state, entered_at_ms, prev_engine_state)
        self._state_since: dict[str, tuple[str, int, str]] = {}

    def update_display_state(self, piece_id: str, engine_state: str, now_ms: int) -> str:
        """Returns the display state to use for this piece right now, handling rest transitions."""
        prev = self._state_since.get(piece_id)

        if prev is None:
            self._state_since[piece_id] = (engine_state, now_ms, engine_state)
            return engine_state

        display_state, entered_at, prev_engine = prev

        # Engine state changed
        if engine_state != prev_engine:
            # Transitioning to idle after a move/jump → play rest first
            rest = _REST_AFTER.get(prev_engine)
            if engine_state == "idle" and rest:
                self._state_since[piece_id] = (rest, now_ms, engine_state)
                return rest
            self._state_since[piece_id] = (engine_state, now_ms, engine_state)
            return engine_state

        # Currently playing a rest animation
        if display_state in ("short_rest", "long_rest"):
            if now_ms - entered_at >= REST_DURATION_MS:
                self._state_since[piece_id] = ("idle", now_ms, engine_state)
                return "idle"
            return display_state
        return display_state

    def frame_index(self, piece_id: str, display_state: str, now_ms: int, frame_count: int) -> int:
        """Returns the frame index (0..frame_count-1) to show for this piece right now."""
        if frame_count <= 0:
            raise ValueError("frame_count must be positive")
        prev = self._state_since.get(piece_id)
        if prev is None or prev[0] != display_state:
            # update_display_state already set the new state — sync entered_at
            self._state_since[piece_id] = (display_state, now_ms, display_state)
            return 0
        elapsed = now_ms - prev[1]
        return (elapsed // FRAME_DURATION_MS) % frame_count

    def folder_state_for(self, display_state: str) -> str:
        """Maps a display state to the CTD26 asset folder-state name."""
        return _STATE_FOLDER.get(display_state, "idle")
