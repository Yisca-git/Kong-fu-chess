"""Tests for server/services/matchmaking.py and server/services/reconnect.py."""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from server.services.matchmaking import MatchmakingQueue, ELO_DELTA, TIMEOUT_S
from server.services.reconnect import ReconnectManager, GRACE_S


# ── helpers ───────────────────────────────────────────────────────────────────

def _ws(name: str = "ws"):
    ws = MagicMock()
    ws.send = AsyncMock()
    ws.__str__ = lambda self: name
    return ws


# ── MatchmakingQueue ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_enqueue_adds_player():
    q = MatchmakingQueue(on_match=AsyncMock())
    q.enqueue("alice", 1200, _ws())
    assert len(q._queue) == 1


@pytest.mark.asyncio
async def test_enqueue_deduplicates():
    q = MatchmakingQueue(on_match=AsyncMock())
    ws = _ws()
    q.enqueue("alice", 1200, ws)
    q.enqueue("alice", 1200, ws)
    assert len(q._queue) == 1


@pytest.mark.asyncio
async def test_dequeue_removes_player():
    q = MatchmakingQueue(on_match=AsyncMock())
    q.enqueue("alice", 1200, _ws())
    q.dequeue("alice")
    assert len(q._queue) == 0


@pytest.mark.asyncio
async def test_match_called_for_close_elo():
    on_match = AsyncMock()
    q = MatchmakingQueue(on_match=on_match)
    q.enqueue("alice", 1200, _ws("a"))
    q.enqueue("bob",   1250, _ws("b"))
    await q._try_match()
    on_match.assert_awaited_once()


@pytest.mark.asyncio
async def test_no_match_for_far_elo():
    on_match = AsyncMock()
    q = MatchmakingQueue(on_match=on_match)
    q.enqueue("alice", 1200, _ws("a"))
    q.enqueue("bob",   1200 + ELO_DELTA + 1, _ws("b"))
    await q._try_match()
    on_match.assert_not_awaited()


@pytest.mark.asyncio
async def test_matched_players_removed_from_queue():
    on_match = AsyncMock()
    q = MatchmakingQueue(on_match=on_match)
    q.enqueue("alice", 1200, _ws("a"))
    q.enqueue("bob",   1200, _ws("b"))
    await q._try_match()
    assert len(q._queue) == 0


@pytest.mark.asyncio
async def test_timeout_removes_player():
    on_match = AsyncMock()
    q = MatchmakingQueue(on_match=on_match)
    ws = _ws()
    q.enqueue("alice", 1200, ws)
    # manually backdate joined_at
    q._queue[0].joined_at -= TIMEOUT_S + 1
    await q._expire_timeouts()
    assert len(q._queue) == 0
    ws.send.assert_awaited_once()


# ── ReconnectManager ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_has_timer_after_start():
    mgr = ReconnectManager(on_forfeit=AsyncMock())
    mgr.start_timer(1, 0)
    assert mgr.has_timer(1, 0)
    mgr.cancel_timer(1, 0)


@pytest.mark.asyncio
async def test_cancel_timer_returns_true_when_active():
    mgr = ReconnectManager(on_forfeit=AsyncMock())
    mgr.start_timer(1, 0)
    assert mgr.cancel_timer(1, 0) is True


@pytest.mark.asyncio
async def test_cancel_timer_returns_false_when_not_active():
    mgr = ReconnectManager(on_forfeit=AsyncMock())
    assert mgr.cancel_timer(99, 0) is False


@pytest.mark.asyncio
async def test_has_timer_false_after_cancel():
    mgr = ReconnectManager(on_forfeit=AsyncMock())
    mgr.start_timer(1, 0)
    mgr.cancel_timer(1, 0)
    assert not mgr.has_timer(1, 0)


@pytest.mark.asyncio
async def test_forfeit_called_after_grace_expires():
    on_forfeit = AsyncMock()
    mgr = ReconnectManager(on_forfeit=on_forfeit)
    # patch GRACE_S to near-zero
    import server.services.reconnect as rc_module
    original = rc_module.GRACE_S
    rc_module.GRACE_S = 0.01
    try:
        mgr.start_timer(1, 0)
        await asyncio.sleep(0.05)
        on_forfeit.assert_awaited_once_with(1, 0)
    finally:
        rc_module.GRACE_S = original


@pytest.mark.asyncio
async def test_start_timer_twice_does_not_duplicate():
    mgr = ReconnectManager(on_forfeit=AsyncMock())
    mgr.start_timer(1, 0)
    mgr.start_timer(1, 0)  # second call should be ignored
    assert len(mgr._timers) == 1
    mgr.cancel_timer(1, 0)
