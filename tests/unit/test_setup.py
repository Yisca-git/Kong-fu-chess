from model.piece import Color, Kind
from model.position import Position
from view.setup import build_starting_board, BOARD_ROWS, BOARD_COLS


def test_board_has_correct_dimensions():
    board, _ = build_starting_board()
    assert board.rows == BOARD_ROWS
    assert board.cols == BOARD_COLS


def test_returns_32_pieces():
    _, pieces = build_starting_board()
    assert len(pieces) == 32


def test_16_white_and_16_black_pieces():
    _, pieces = build_starting_board()
    assert sum(1 for p in pieces if p.color == Color.WHITE) == 16
    assert sum(1 for p in pieces if p.color == Color.BLACK) == 16


def test_8_pawns_per_side():
    _, pieces = build_starting_board()
    white_pawns = [p for p in pieces if p.color == Color.WHITE and p.kind == Kind.PAWN]
    black_pawns = [p for p in pieces if p.color == Color.BLACK and p.kind == Kind.PAWN]
    assert len(white_pawns) == 8
    assert len(black_pawns) == 8


def test_white_pawns_on_row_6():
    _, pieces = build_starting_board()
    for p in pieces:
        if p.color == Color.WHITE and p.kind == Kind.PAWN:
            assert p.cell.row == 6


def test_black_pawns_on_row_1():
    _, pieces = build_starting_board()
    for p in pieces:
        if p.color == Color.BLACK and p.kind == Kind.PAWN:
            assert p.cell.row == 1


def test_white_back_rank_on_row_7():
    _, pieces = build_starting_board()
    back = [p for p in pieces if p.color == Color.WHITE and p.kind != Kind.PAWN]
    assert all(p.cell.row == 7 for p in back)


def test_black_back_rank_on_row_0():
    _, pieces = build_starting_board()
    back = [p for p in pieces if p.color == Color.BLACK and p.kind != Kind.PAWN]
    assert all(p.cell.row == 0 for p in back)


def test_kings_on_correct_columns():
    _, pieces = build_starting_board()
    white_king = next(p for p in pieces if p.color == Color.WHITE and p.kind == Kind.KING)
    black_king = next(p for p in pieces if p.color == Color.BLACK and p.kind == Kind.KING)
    assert white_king.cell == Position(7, 4)
    assert black_king.cell == Position(0, 4)


def test_all_pieces_are_on_the_board():
    board, pieces = build_starting_board()
    for piece in pieces:
        assert board.piece_at(piece.cell) is piece


def test_no_two_pieces_share_a_cell():
    _, pieces = build_starting_board()
    cells = [p.cell for p in pieces]
    assert len(cells) == len(set(cells))


def test_all_piece_ids_are_unique():
    _, pieces = build_starting_board()
    ids = [p.id for p in pieces]
    assert len(ids) == len(set(ids))
