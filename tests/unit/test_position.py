import pytest
from model.position import Position


def test_equal_same_row_and_col():
    assert Position(3, 4) == Position(3, 4)


def test_not_equal_different_row():
    assert Position(3, 4) != Position(2, 4)


def test_not_equal_different_col():
    assert Position(3, 4) != Position(3, 5)


def test_negative_row_raises():
    with pytest.raises(ValueError, match=r"\(-1, 0\)"):
        Position(-1, 0)


def test_negative_col_raises():
    with pytest.raises(ValueError, match=r"\(0, -1\)"):
        Position(0, -1)
