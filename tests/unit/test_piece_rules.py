import pytest
from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from rules.rook_rules import RookRules
from rules.bishop_rules import BishopRules
from rules.queen_rules import QueenRules
from rules.knight_rules import KnightRules
from rules.king_rules import KingRules
from rules.pawn_rules import PawnRules


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def empty_board():
    return Board(8, 8)


def place(board, *pieces):
    for p in pieces:
        board.add_piece(p)


# --- Rook ---

def test_rook_slides_along_empty_row_and_col():
    board = empty_board()
    rook = make_piece(4, 4)
    place(board, rook)
    dests = RookRules().legal_destinations(board, rook)
    assert Position(4, 0) in dests
    assert Position(4, 7) in dests
    assert Position(0, 4) in dests
    assert Position(7, 4) in dests


def test_rook_blocked_by_friendly():
    board = empty_board()
    rook = make_piece(4, 4)
    blocker = make_piece(4, 6, kind=Kind.BISHOP)
    place(board, rook, blocker)
    dests = RookRules().legal_destinations(board, rook)
    assert Position(4, 5) in dests
    assert Position(4, 6) not in dests
    assert Position(4, 7) not in dests


def test_rook_captures_enemy_but_not_beyond():
    board = empty_board()
    rook = make_piece(4, 4)
    enemy = make_piece(4, 6, color=Color.BLACK)
    place(board, rook, enemy)
    dests = RookRules().legal_destinations(board, rook)
    assert Position(4, 6) in dests
    assert Position(4, 7) not in dests


# --- Bishop ---

def test_bishop_moves_diagonally():
    board = empty_board()
    bishop = make_piece(4, 4, kind=Kind.BISHOP)
    place(board, bishop)
    dests = BishopRules().legal_destinations(board, bishop)
    assert Position(7, 7) in dests
    assert Position(1, 1) in dests
    assert Position(4, 5) not in dests
    assert Position(5, 4) not in dests


# --- Queen ---

def test_queen_combines_rook_and_bishop():
    board = empty_board()
    queen = make_piece(4, 4, kind=Kind.QUEEN)
    place(board, queen)
    dests = QueenRules().legal_destinations(board, queen)
    assert Position(4, 7) in dests   # rook
    assert Position(7, 7) in dests   # bishop


# --- Knight ---

def test_knight_jumps_over_blockers():
    board = empty_board()
    knight = make_piece(4, 4, kind=Kind.KNIGHT)
    blocker1 = make_piece(4, 5, kind=Kind.BISHOP)
    blocker2 = make_piece(5, 4, kind=Kind.BISHOP)
    place(board, knight, blocker1, blocker2)
    dests = KnightRules().legal_destinations(board, knight)
    assert Position(2, 3) in dests
    assert Position(2, 5) in dests
    assert Position(6, 3) in dests
    assert Position(6, 5) in dests


# --- King ---

def test_king_moves_one_square_only():
    board = empty_board()
    king = make_piece(4, 4, kind=Kind.KING)
    place(board, king)
    dests = KingRules().legal_destinations(board, king)
    assert dests == {
        Position(3, 3), Position(3, 4), Position(3, 5),
        Position(4, 3),                 Position(4, 5),
        Position(5, 3), Position(5, 4), Position(5, 5),
    }


# --- Pawn ---

def test_pawn_moves_forward():
    board = empty_board()
    pawn = make_piece(4, 4, kind=Kind.PAWN)
    place(board, pawn)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(3, 4) in dests


def test_pawn_double_step_from_start_row():
    board = empty_board()
    pawn = make_piece(6, 4, kind=Kind.PAWN)
    place(board, pawn)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(4, 4) in dests


def test_pawn_captures_diagonally():
    board = empty_board()
    pawn = make_piece(4, 4, kind=Kind.PAWN)
    enemy = make_piece(3, 5, kind=Kind.PAWN, color=Color.BLACK)
    place(board, pawn, enemy)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(3, 5) in dests


def test_pawn_cannot_capture_forward():
    board = empty_board()
    pawn = make_piece(4, 4, kind=Kind.PAWN)
    blocker = make_piece(3, 4, kind=Kind.PAWN, color=Color.BLACK)
    place(board, pawn, blocker)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(3, 4) not in dests


def test_pawn_double_step_blocked_by_intermediate_piece():
    board = empty_board()
    pawn = make_piece(6, 4, kind=Kind.PAWN)
    blocker = make_piece(5, 4, kind=Kind.PAWN, color=Color.BLACK)
    place(board, pawn, blocker)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(5, 4) not in dests
    assert Position(4, 4) not in dests


def test_pawn_double_step_not_available_from_non_start_row():
    board = empty_board()
    pawn = make_piece(4, 4, kind=Kind.PAWN)
    place(board, pawn)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(2, 4) not in dests


# --- Black Pawn ---

def test_black_pawn_moves_forward_down():
    board = empty_board()
    pawn = make_piece(3, 4, kind=Kind.PAWN, color=Color.BLACK)
    place(board, pawn)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(4, 4) in dests


def test_black_pawn_double_step_from_start_row():
    board = empty_board()
    pawn = make_piece(1, 4, kind=Kind.PAWN, color=Color.BLACK)
    place(board, pawn)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(3, 4) in dests


def test_black_pawn_captures_diagonally_down():
    board = empty_board()
    pawn = make_piece(3, 4, kind=Kind.PAWN, color=Color.BLACK)
    enemy = make_piece(4, 5, kind=Kind.PAWN, color=Color.WHITE)
    place(board, pawn, enemy)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(4, 5) in dests


def test_black_pawn_cannot_capture_forward():
    board = empty_board()
    pawn = make_piece(3, 4, kind=Kind.PAWN, color=Color.BLACK)
    blocker = make_piece(4, 4, kind=Kind.PAWN, color=Color.WHITE)
    place(board, pawn, blocker)
    dests = PawnRules().legal_destinations(board, pawn)
    assert Position(4, 4) not in dests


# --- Pawn promotion ---

def test_white_pawn_promotes_to_queen_on_row_0():
    pawn = make_piece(0, 4, kind=Kind.PAWN)
    PawnRules().on_arrival(pawn, board_rows=8)
    assert pawn.kind == Kind.QUEEN


def test_black_pawn_promotes_to_queen_on_last_row():
    pawn = make_piece(7, 4, kind=Kind.PAWN, color=Color.BLACK)
    PawnRules().on_arrival(pawn, board_rows=8)
    assert pawn.kind == Kind.QUEEN


def test_pawn_does_not_promote_mid_board():
    pawn = make_piece(4, 4, kind=Kind.PAWN)
    PawnRules().on_arrival(pawn, board_rows=8)
    assert pawn.kind == Kind.PAWN


# --- Sliding (direct) ---

def test_slide_stops_at_board_edge():
    from rules.sliding import slide
    board = empty_board()
    rook = make_piece(0, 0)
    place(board, rook)
    dests = slide(board, rook, [(0, 1)])
    assert Position(0, 7) in dests
    assert all(d.col <= 7 for d in dests)


def test_slide_includes_enemy_but_not_beyond():
    from rules.sliding import slide
    board = empty_board()
    rook = make_piece(0, 0)
    enemy = make_piece(0, 3, color=Color.BLACK)
    place(board, rook, enemy)
    dests = slide(board, rook, [(0, 1)])
    assert Position(0, 3) in dests
    assert Position(0, 4) not in dests


def test_slide_excludes_friendly():
    from rules.sliding import slide
    board = empty_board()
    rook = make_piece(0, 0)
    friendly = make_piece(0, 3, kind=Kind.BISHOP)
    place(board, rook, friendly)
    dests = slide(board, rook, [(0, 1)])
    assert Position(0, 3) not in dests
    assert Position(0, 4) not in dests
