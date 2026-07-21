import pytest
from unittest.mock import MagicMock
from input.controller import Controller
from model.position import Position

CELL = 100


def make_controller(piece_at=False):
    engine = MagicMock()
    engine.piece_at.return_value = piece_at
    return Controller(engine, 8, 8, cell_size=CELL), engine


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


def test_jump_out_of_bounds_does_not_call_engine():
    ctrl, engine = make_controller()
    engine.in_bounds.return_value = False
    ctrl.handle_jump(9 * CELL, 9 * CELL)
    engine.request_jump.assert_not_called()


def test_jump_out_of_bounds_clears_selection():
    ctrl, engine = make_controller(piece_at=True)
    ctrl.handle_click(0, 0)              # select
    ctrl.handle_jump(9 * CELL, 9 * CELL) # out of bounds
    assert ctrl._selected is None


def test_rejected_move_non_friendly_clears_selection():
    ctrl, engine = make_controller(piece_at=True)
    from engine.move_result import MoveResult
    engine.request_move.return_value = MoveResult(False, MoveResult.PIECE_ON_COOLDOWN)
    ctrl.handle_click(0, 0)
    ctrl.handle_click(2 * CELL, 0)
    engine.set_rejection.assert_called_with(MoveResult.PIECE_ON_COOLDOWN)
    assert ctrl._selected is None


def test_click_on_empty_cell_when_nothing_selected_does_nothing():
    ctrl, engine = make_controller(piece_at=False)
    ctrl.handle_click(3 * CELL, 3 * CELL)
    engine.request_move.assert_not_called()
    assert ctrl._selected is None
