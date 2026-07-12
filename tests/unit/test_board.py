import pytest
from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id="p1", color=color, kind=kind, cell=Position(row, col))


def test_board_dimensions():
    board = Board(8, 8)
    assert board.rows == 8 and board.cols == 8


def test_empty_cell_returns_none():
    board = Board(8, 8)
    assert board.piece_at(Position(0, 0)) is None


def test_occupied_cell_returns_piece():
    board = Board(8, 8)
    piece = make_piece(0, 0)
    board.add_piece(piece)
    assert board.piece_at(Position(0, 0)) is piece


def test_add_two_pieces_same_cell_raises():
    board = Board(8, 8)
    board.add_piece(make_piece(0, 0))
    with pytest.raises(ValueError):
        board.add_piece(make_piece(0, 0, kind=Kind.BISHOP))


def test_move_piece_updates_source_and_destination():
    board = Board(8, 8)
    piece = make_piece(0, 0)
    board.add_piece(piece)
    board.move_piece(piece, Position(3, 3))
    assert board.piece_at(Position(0, 0)) is None
    assert board.piece_at(Position(3, 3)) is piece


def test_remove_piece_clears_cell():
    board = Board(8, 8)
    piece = make_piece(0, 0)
    board.add_piece(piece)
    board.remove_piece(Position(0, 0))
    assert board.piece_at(Position(0, 0)) is None
