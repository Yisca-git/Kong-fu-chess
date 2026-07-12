import pytest
from input.board_mapper import pixel_to_position, CELL_SIZE
from model.position import Position


def test_origin():
    assert pixel_to_position(0, 0) == Position(0, 0)


def test_within_first_cell():
    assert pixel_to_position(CELL_SIZE - 1, CELL_SIZE - 1) == Position(0, 0)


def test_second_cell():
    assert pixel_to_position(CELL_SIZE, CELL_SIZE) == Position(1, 1)


def test_arbitrary_pixel():
    assert pixel_to_position(250, 350) == Position(3, 2)
