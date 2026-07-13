import pytest
from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from rules.rule_engine import RuleEngine


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def board_with(*pieces):
    board = Board(8, 8)
    for p in pieces:
        board.add_piece(p)
    return board


engine = RuleEngine()


def test_rejects_source_outside_board():
    board = Board(8, 8)
    result = engine.validate(board, Position(0, 0), Position(9, 0))
    assert not result.is_valid
    assert result.reason == "outside_board"


def test_rejects_empty_source():
    board = Board(8, 8)
    result = engine.validate(board, Position(0, 0), Position(1, 0))
    assert not result.is_valid
    assert result.reason == "empty_source"


def test_rejects_friendly_destination():
    rook = make_piece(0, 0)
    blocker = make_piece(0, 4, kind=Kind.BISHOP)
    board = board_with(rook, blocker)
    result = engine.validate(board, Position(0, 0), Position(0, 4))
    assert not result.is_valid
    assert result.reason == "friendly_destination"


def test_rejects_illegal_piece_move():
    rook = make_piece(0, 0)
    board = board_with(rook)
    result = engine.validate(board, Position(0, 0), Position(1, 1))
    assert not result.is_valid
    assert result.reason == "illegal_piece_move"


def test_accepts_valid_move():
    rook = make_piece(0, 0)
    board = board_with(rook)
    result = engine.validate(board, Position(0, 0), Position(0, 4))
    assert result.is_valid
    assert result.reason == "ok"


def test_accepts_capture_of_enemy():
    rook = make_piece(0, 0)
    enemy = make_piece(0, 4, color=Color.BLACK)
    board = board_with(rook, enemy)
    result = engine.validate(board, Position(0, 0), Position(0, 4))
    assert result.is_valid
    assert result.reason == "ok"


def test_rejects_friendly_airborne_destination():
    rook = make_piece(0, 0)
    board = board_with(rook)
    result = engine.validate(board, Position(0, 0), Position(0, 4), friendly_airborne={Position(0, 4)})
    assert not result.is_valid
    assert result.reason == "friendly_airborne_destination"


def test_moving_origin_does_not_block_path():
    rook = make_piece(0, 0)
    blocker = make_piece(0, 2)
    board = board_with(rook, blocker)
    result = engine.validate(board, Position(0, 0), Position(0, 4), moving_origins={Position(0, 2)})
    assert result.is_valid
