"""Tests for server/core/game_session.py."""
import asyncio
import pytest
from unittest.mock import MagicMock, patch
from server.core.game_session import GameSession


def _make_session(**kwargs) -> GameSession:
    return GameSession(on_state=MagicMock(), on_game_over=MagicMock(), **kwargs)


# ── init ──────────────────────────────────────────────────────────────────────

def test_session_engine_not_game_over_initially():
    s = _make_session()
    assert not s.engine.game_over


def test_session_task_is_none_before_start():
    s = _make_session()
    assert s._task is None


def test_session_custom_names():
    s = _make_session(white_name="Alice", black_name="Bob")
    snap = s.engine.snapshot()
    assert snap.white_name == "Alice"
    assert snap.black_name == "Bob"


# ── start / stop ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_start_creates_task():
    s = _make_session()
    s.start()
    assert s._task is not None
    s.stop()
    await asyncio.sleep(0)  # let cancellation propagate


@pytest.mark.asyncio
async def test_stop_cancels_task():
    s = _make_session()
    s.start()
    s.stop()
    await asyncio.sleep(0)
    assert s._task.cancelled() or s._task.done()


@pytest.mark.asyncio
async def test_on_state_called_each_tick():
    on_state = MagicMock()
    s = GameSession(on_state=on_state, on_game_over=MagicMock())
    s.start()
    await asyncio.sleep(0.1)
    s.stop()
    assert on_state.call_count >= 1


# ── engine access ─────────────────────────────────────────────────────────────

def test_engine_property_returns_game_engine():
    from engine.game_engine import GameEngine
    s = _make_session()
    assert isinstance(s.engine, GameEngine)
