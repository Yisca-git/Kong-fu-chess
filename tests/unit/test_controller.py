import pytest
from unittest.mock import MagicMock
from input.controller import Controller
from model.position import Position

CELL = 100


def make_controller(piece_at=False):
    engine = MagicMock()
    engine.piece_at.return_value = piece_at
    return Controller(engine, 8, 8), engine


def test_click_out_of_bounds_clears_selection():
    ctrl, engine = make_controller(piece_at=True)
    ctrl.handle_click(0, 0)                  # select piece at (0,0)
    ctrl.handle_click(9 * CELL, 9 * CELL)    # out of bounds
    assert ctrl._selected is None


def test_click_selects_piece():
    ctrl, engine = make_controller(piece_at=True)
    ctrl.handle_click(0, 0)
    assert ctrl._selected == Position(0, 0)


def test_click_empty_cell_does_not_select():
    ctrl, engine = make_controller(piece_at=False)
    ctrl.handle_click(0, 0)
    assert ctrl._selected is None


def test_second_click_issues_move_and_clears_selection():
    ctrl, engine = make_controller(piece_at=True)
    ctrl.handle_click(0, 0)
    ctrl.handle_click(2 * CELL, 3 * CELL)
    engine.request_move.assert_called_once_with(Position(0, 0), Position(3, 2))
    assert ctrl._selected is None


def test_jump_in_bounds():
    ctrl, engine = make_controller()
    ctrl.handle_jump(CELL, CELL)
    engine.request_jump.assert_called_once_with(Position(1, 1))


def test_friendly_destination_reselects():
    ctrl, engine = make_controller(piece_at=True)
    from engine.move_result import MoveResult
    engine.request_move.return_value = MoveResult(False, MoveResult.FRIENDLY_DESTINATION)
    ctrl.handle_click(0, 0)
    ctrl.handle_click(2 * CELL, 0)
    assert ctrl._selected == Position(0, 2)


def test_non_friendly_result_clears_selection():
    ctrl, engine = make_controller(piece_at=True)
    from engine.move_result import MoveResult
    engine.request_move.return_value = MoveResult(True, MoveResult.OK)
    ctrl.handle_click(0, 0)
    ctrl.handle_click(2 * CELL, 0)
    assert ctrl._selected is None
