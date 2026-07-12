import pytest
from text_io.board_parser import parse, validate
from model.piece import Color, Kind, PieceState

SIMPLE_TEXT = """\
Board:
wR .
.  bK
Commands:
"""


def test_parse_board_dimensions():
    board, _ = parse(SIMPLE_TEXT)
    assert board.rows == 2 and board.cols == 2


def test_parse_pieces_count():
    _, pieces = parse(SIMPLE_TEXT)
    assert len(pieces) == 2


def test_parse_piece_attributes():
    _, pieces = parse(SIMPLE_TEXT)
    rook = next(p for p in pieces if p.kind == Kind.ROOK)
    assert rook.color == Color.WHITE
    assert rook.cell.row == 0 and rook.cell.col == 0
    assert rook.state == PieceState.IDLE


def test_parse_empty_cell_skipped():
    _, pieces = parse(SIMPLE_TEXT)
    assert all(p.kind != Kind.PAWN for p in pieces)


def test_validate_valid():
    assert validate(SIMPLE_TEXT) is True


def test_validate_unknown_token(capsys):
    bad = "Board:\nXX .\nCommands:\n"
    assert validate(bad) is False
    assert "ERROR" in capsys.readouterr().out


def test_validate_row_width_mismatch(capsys):
    bad = "Board:\nwR . bK\n. .\nCommands:\n"
    assert validate(bad) is False
    assert "ERROR" in capsys.readouterr().out


def test_duplicate_piece_ids_are_unique():
    text = "Board:\nwR wR\nCommands:\n"
    _, pieces = parse(text)
    ids = [p.id for p in pieces]
    assert len(ids) == len(set(ids))
