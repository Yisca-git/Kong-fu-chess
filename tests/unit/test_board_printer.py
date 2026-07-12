import pytest
from text_io.board_printer import print_board
from engine.game_snapshot import GameSnapshot, PieceSnapshot


def make_snapshot(pieces, rows=2, cols=2):
    return GameSnapshot(tuple(pieces), False, rows, cols)


def test_empty_board(capsys):
    snap = make_snapshot([])
    print_board(snap)
    assert capsys.readouterr().out == ". .\n. .\n"


def test_single_piece(capsys):
    snap = make_snapshot([PieceSnapshot("wR1", "w", "R", 0, 0)])
    print_board(snap)
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "wR . "  or lines[0].startswith("wR")


def test_piece_position(capsys):
    snap = make_snapshot([PieceSnapshot("bK1", "b", "K", 1, 1)])
    print_board(snap)
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == ". ."
    assert lines[1].endswith("bK")


def test_multiple_pieces(capsys):
    pieces = [
        PieceSnapshot("wR1", "w", "R", 0, 0),
        PieceSnapshot("bK1", "b", "K", 1, 1),
    ]
    snap = make_snapshot(pieces)
    print_board(snap)
    lines = capsys.readouterr().out.splitlines()
    assert "wR" in lines[0]
    assert "bK" in lines[1]
