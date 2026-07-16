import pytest
from unittest.mock import MagicMock
from view.sprites.sprite_state import StateConfig, SpriteState, AnimatedSprite


def make_config(name="idle", fps=10.0, is_loop=True, next_state=None):
    return StateConfig(name=name, frames_per_sec=fps, is_loop=is_loop,
                       next_state_when_finished=next_state)


def make_frames(n=5):
    return [MagicMock() for _ in range(n)]


# ── SpriteState ──────────────────────────────────────────────────────────────

def test_sprite_state_raises_with_no_frames():
    with pytest.raises(ValueError):
        SpriteState(make_config(), frames=[])


def test_initial_frame_is_zero():
    frames = make_frames(5)
    state = SpriteState(make_config(fps=10, is_loop=True), frames)
    assert state.current_frame is frames[0]


def test_advance_moves_frame_forward():
    frames = make_frames(5)
    state  = SpriteState(make_config(fps=10, is_loop=True), frames)
    state.advance(200)   # 200ms @ 10fps = 2 frames
    assert state.current_frame is frames[2]


def test_looping_state_wraps_around():
    frames = make_frames(3)
    state  = SpriteState(make_config(fps=10, is_loop=True), frames)
    state.advance(300)   # 3 frames → wraps to 0
    assert state.current_frame is frames[0]


def test_non_looping_state_clamps_at_last_frame():
    frames = make_frames(3)
    state  = SpriteState(make_config(fps=10, is_loop=False), frames)
    state.advance(9999)
    assert state.current_frame is frames[-1]


def test_non_looping_is_finished_after_full_duration():
    frames = make_frames(3)
    state  = SpriteState(make_config(fps=10, is_loop=False), frames)
    state.advance(300)   # 3 frames × 100ms = 300ms
    assert state.is_finished


def test_looping_state_never_finishes():
    state = SpriteState(make_config(is_loop=True), make_frames())
    state.advance(99999)
    assert not state.is_finished


def test_reset_restarts_clock():
    frames = make_frames(5)
    state  = SpriteState(make_config(fps=10, is_loop=True), frames)
    state.advance(300)
    state.reset()
    assert state.current_frame is frames[0]


# ── AnimatedSprite ────────────────────────────────────────────────────────────

def _make_library(states: dict[str, SpriteState]):
    """Returns a fake SpriteLibrary that serves from a pre-built dict."""
    lib = MagicMock()
    lib.get_state.side_effect = lambda color, kind, engine_state: states[engine_state]
    return lib


def test_animated_sprite_starts_in_initial_state():
    idle  = SpriteState(make_config("idle", fps=10, is_loop=True), make_frames())
    lib   = _make_library({"idle": idle})
    sprite = AnimatedSprite(lib, "W", "P", initial_state="idle")
    assert sprite.current_frame is idle.current_frame


def test_animated_sprite_transitions_on_engine_state_change():
    frames_idle = make_frames(3)
    frames_move = make_frames(3)
    idle = SpriteState(make_config("idle", fps=10, is_loop=True),  frames_idle)
    move = SpriteState(make_config("move", fps=10, is_loop=True),  frames_move)
    lib  = _make_library({"idle": idle, "moving": move})

    sprite = AnimatedSprite(lib, "W", "P", initial_state="idle")
    sprite.update(100, "moving")
    assert sprite.current_frame is frames_move[0]


def test_animated_sprite_auto_transitions_when_non_looping_finishes():
    frames_jump = make_frames(2)
    frames_rest = make_frames(3)
    jump = SpriteState(make_config("jump", fps=10, is_loop=False, next_state="short_rest"), frames_jump)
    rest = SpriteState(make_config("short_rest", fps=10, is_loop=False), frames_rest)
    lib  = _make_library({"airborne": jump, "short_rest": rest})

    sprite = AnimatedSprite(lib, "W", "P", initial_state="airborne")
    sprite.update(200, "airborne")   # 2 frames × 100ms → finished, auto-transitions to short_rest
    assert sprite.current_frame is frames_rest[0]


def test_animated_sprite_inserts_short_rest_after_moving_to_idle():
    frames_move = make_frames(2)
    frames_rest = make_frames(3)
    frames_idle = make_frames(3)
    move = SpriteState(make_config("move", fps=10, is_loop=False), frames_move)
    rest = SpriteState(make_config("short_rest", fps=10, is_loop=False, next_state="idle"), frames_rest)
    idle = SpriteState(make_config("idle", fps=10, is_loop=True), frames_idle)
    lib  = _make_library({"moving": move, "short_rest": rest, "idle": idle})

    sprite = AnimatedSprite(lib, "W", "P", initial_state="moving")
    sprite.update(0, "idle")   # engine transitions moving -> idle
    assert sprite.current_frame is frames_rest[0]  # should be in short_rest, not idle


def test_animated_sprite_inserts_long_rest_after_airborne_to_idle():
    frames_jump = make_frames(2)
    frames_rest = make_frames(3)
    frames_idle = make_frames(3)
    jump = SpriteState(make_config("jump", fps=10, is_loop=False), frames_jump)
    rest = SpriteState(make_config("long_rest", fps=10, is_loop=False, next_state="idle"), frames_rest)
    idle = SpriteState(make_config("idle", fps=10, is_loop=True), frames_idle)
    lib  = _make_library({"airborne": jump, "long_rest": rest, "idle": idle})

    sprite = AnimatedSprite(lib, "W", "P", initial_state="airborne")
    sprite.update(0, "idle")   # engine transitions airborne -> idle
    assert sprite.current_frame is frames_rest[0]  # should be in long_rest, not idle


def test_animated_sprite_no_rest_for_non_rest_transition():
    frames_idle = make_frames(3)
    frames_move = make_frames(3)
    idle = SpriteState(make_config("idle", fps=10, is_loop=True), frames_idle)
    move = SpriteState(make_config("move", fps=10, is_loop=False), frames_move)
    lib  = _make_library({"idle": idle, "moving": move})

    sprite = AnimatedSprite(lib, "W", "P", initial_state="idle")
    sprite.update(0, "moving")  # idle -> moving: no rest
    assert sprite.current_frame is frames_move[0]


def test_animated_sprite_kind_property():
    idle   = SpriteState(make_config("idle", fps=10, is_loop=True), make_frames())
    lib    = _make_library({"idle": idle})
    sprite = AnimatedSprite(lib, "w", "P", initial_state="idle")
    assert sprite.kind == "P"


def test_animated_sprite_advances_frame_over_time():
    frames = make_frames(5)
    idle   = SpriteState(make_config("idle", fps=10, is_loop=True), frames)
    lib    = _make_library({"idle": idle})
    sprite = AnimatedSprite(lib, "W", "P", initial_state="idle")
    sprite.update(200, "idle")
    assert sprite.current_frame is frames[2]
