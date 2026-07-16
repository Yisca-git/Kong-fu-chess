from unittest.mock import MagicMock
from engine.game_snapshot import GameSnapshot
from view.rendering.board_view import BoardView
from view.img import Img
import numpy as np


def _blank_img(w=800, h=800) -> Img:
    img = Img()
    img.img = np.zeros((h, w, 3), dtype=np.uint8)
    return img


def _snapshot(**kwargs) -> GameSnapshot:
    defaults = dict(pieces=(), game_over=False, rows=8, cols=8)
    defaults.update(kwargs)
    return GameSnapshot(**defaults)


def _make_collaborators():
    board   = MagicMock()
    board.fresh_frame.return_value = _blank_img()

    pieces  = MagicMock()

    overlay = MagicMock()
    overlay.compose_panels.return_value = _blank_img()

    return board, pieces, overlay


# ── BoardView delegates correctly ────────────────────────────────────────────

def test_render_calls_fresh_frame_with_board_dimensions():
    board, pieces, overlay = _make_collaborators()
    view = BoardView(board, pieces, overlay)
    view.render(_snapshot(rows=8, cols=8), dt_ms=16)
    board.fresh_frame.assert_called_once_with(8, 8)


def test_render_calls_draw_selection():
    board, pieces, overlay = _make_collaborators()
    view     = BoardView(board, pieces, overlay)
    snapshot = _snapshot()
    view.render(snapshot, dt_ms=16)
    overlay.draw_selection.assert_called_once()


def test_render_calls_piece_draw():
    board, pieces, overlay = _make_collaborators()
    view     = BoardView(board, pieces, overlay)
    snapshot = _snapshot()
    view.render(snapshot, dt_ms=16)
    pieces.draw.assert_called_once()


def test_render_calls_compose_panels():
    board, pieces, overlay = _make_collaborators()
    view     = BoardView(board, pieces, overlay)
    snapshot = _snapshot()
    view.render(snapshot, dt_ms=16)
    overlay.compose_panels.assert_called_once()


def test_render_does_not_call_game_over_when_not_over():
    board, pieces, overlay = _make_collaborators()
    view = BoardView(board, pieces, overlay)
    view.render(_snapshot(game_over=False), dt_ms=16)
    overlay.draw_game_over.assert_not_called()


def test_render_calls_game_over_when_over():
    board, pieces, overlay = _make_collaborators()
    view = BoardView(board, pieces, overlay)
    view.render(_snapshot(game_over=True, winner="w"), dt_ms=16)
    overlay.draw_game_over.assert_called_once()


def test_render_returns_img_from_compose_panels():
    board, pieces, overlay = _make_collaborators()
    expected = _blank_img()
    overlay.compose_panels.return_value = expected
    view   = BoardView(board, pieces, overlay)
    result = view.render(_snapshot(), dt_ms=16)
    assert result is expected
