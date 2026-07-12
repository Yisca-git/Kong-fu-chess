from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rules_registry import RULES_BY_KIND


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def setup(pieces):
    board = Board(8, 8)
    for p in pieces:
        board.add_piece(p)
    return board, RealTimeArbiter(board, RULES_BY_KIND)


# --- timing ---

def test_one_step_takes_1000ms():
    rook = make_piece(0, 0)
    board, arbiter = setup([rook])
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(999)
    assert board.piece_at(Position(0, 0)) is rook
    arbiter.advance_time(1)
    assert board.piece_at(Position(0, 1)) is rook


def test_two_steps_take_2000ms():
    rook = make_piece(0, 0)
    board, arbiter = setup([rook])
    arbiter.start_motion(rook, Position(0, 2))
    arbiter.advance_time(1999)
    assert board.piece_at(Position(0, 0)) is rook
    arbiter.advance_time(1)
    assert board.piece_at(Position(0, 2)) is rook


def test_diagonal_uses_chebyshev_distance():
    bishop = make_piece(0, 0, kind=Kind.BISHOP)
    board, arbiter = setup([bishop])
    arbiter.start_motion(bishop, Position(3, 3))
    arbiter.advance_time(2999)
    assert board.piece_at(Position(0, 0)) is bishop
    arbiter.advance_time(1)
    assert board.piece_at(Position(3, 3)) is bishop


# --- logical board state ---

def test_piece_stays_on_source_until_arrival():
    rook = make_piece(0, 0)
    board, arbiter = setup([rook])
    arbiter.start_motion(rook, Position(0, 4))
    arbiter.advance_time(2000)
    assert board.piece_at(Position(0, 0)) is rook
    assert board.piece_at(Position(0, 4)) is None


def test_piece_moves_to_destination_on_arrival():
    rook = make_piece(0, 0)
    board, arbiter = setup([rook])
    arbiter.start_motion(rook, Position(0, 4))
    arbiter.advance_time(4000)
    assert board.piece_at(Position(0, 0)) is None
    assert board.piece_at(Position(0, 4)) is rook


# --- capture ---

def test_arrival_captures_enemy():
    rook = make_piece(0, 0)
    enemy = make_piece(0, 1, color=Color.BLACK)
    board, arbiter = setup([rook, enemy])
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000)
    assert board.piece_at(Position(0, 1)) is rook
    assert enemy.state == PieceState.CAPTURED


def test_arrival_captures_king_sets_game_over():
    rook = make_piece(0, 0)
    king = make_piece(0, 1, kind=Kind.KING, color=Color.BLACK)
    board, arbiter = setup([rook, king])
    arbiter.start_motion(rook, Position(0, 1))
    king_captured = arbiter.advance_time(1000)
    assert king_captured


# --- jump ---

def test_jump_removes_piece_from_board():
    rook = make_piece(0, 0)
    board, arbiter = setup([rook])
    arbiter.start_jump(rook)
    assert board.piece_at(Position(0, 0)) is None


def test_piece_lands_back_after_jump_duration():
    rook = make_piece(0, 0)
    board, arbiter = setup([rook])
    arbiter.start_jump(rook)
    arbiter.advance_time(1000)
    assert board.piece_at(Position(0, 0)) is rook
