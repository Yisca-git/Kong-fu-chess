from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rules_registry import RULES_BY_KIND
from engine.arrival_resolver import ArrivalResolver


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def setup(pieces):
    board    = Board(8, 8)
    for p in pieces:
        board.add_piece(p)
    arbiter  = RealTimeArbiter()
    resolver = ArrivalResolver(board, RULES_BY_KIND, arbiter)
    return board, arbiter, resolver


# --- logical board state ---

def test_piece_stays_on_source_until_arrival():
    rook = make_piece(0, 0)
    board, arbiter, resolver = setup([rook])
    arbiter.start_motion(rook, Position(0, 4))
    arbiter.advance_time(2000, resolver)
    assert board.piece_at(Position(0, 0)) is rook
    assert board.piece_at(Position(0, 4)) is None


def test_piece_moves_to_destination_on_arrival():
    rook = make_piece(0, 0)
    board, arbiter, resolver = setup([rook])
    arbiter.start_motion(rook, Position(0, 4))
    arbiter.advance_time(4000, resolver)
    assert board.piece_at(Position(0, 0)) is None
    assert board.piece_at(Position(0, 4)) is rook


# --- capture ---

def test_arrival_captures_enemy():
    rook = make_piece(0, 0)
    enemy = make_piece(0, 1, color=Color.BLACK)
    board, arbiter, resolver = setup([rook, enemy])
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)
    assert board.piece_at(Position(0, 1)) is rook
    assert enemy.state == PieceState.CAPTURED


def test_arrival_captures_king_sets_game_over():
    rook = make_piece(0, 0)
    king = make_piece(0, 1, kind=Kind.KING, color=Color.BLACK)
    board, arbiter, resolver = setup([rook, king])
    arbiter.start_motion(rook, Position(0, 1))
    king_captured = arbiter.advance_time(1000, resolver)
    assert king_captured


# --- jump landing ---

def test_piece_lands_back_after_jump_duration():
    rook = make_piece(0, 0)
    board, arbiter, resolver = setup([rook])
    arbiter.start_jump(rook)
    board.remove_piece(Position(0, 0))  # GameEngine performs this immediate removal, not the arbiter
    arbiter.advance_time(1000, resolver)
    assert board.piece_at(Position(0, 0)) is rook


# --- cooldown, applied via the resolver ---

def test_piece_on_cooldown_after_arrival():
    rook = make_piece(0, 0)
    board, arbiter, resolver = setup([rook])
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)  # arrival
    assert arbiter.is_piece_on_cooldown(rook)


def test_piece_not_on_cooldown_after_cooldown_expires():
    rook = make_piece(0, 0)
    board, arbiter, resolver = setup([rook])
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(2000, resolver)  # arrival + cooldown
    assert not arbiter.is_piece_on_cooldown(rook)


def test_piece_on_cooldown_after_jump_landing():
    rook = make_piece(0, 0)
    board, arbiter, resolver = setup([rook])
    arbiter.start_jump(rook)
    board.remove_piece(Position(0, 0))
    arbiter.advance_time(1000, resolver)  # landing
    assert arbiter.is_piece_on_cooldown(rook)


# --- friendly destination ---

def test_arrival_at_friendly_destination_returns_piece_to_origin():
    rook = make_piece(0, 0)
    friendly = make_piece(0, 1, kind=Kind.BISHOP)
    board, arbiter, resolver = setup([rook, friendly])
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)
    assert board.piece_at(Position(0, 0)) is rook
    assert board.piece_at(Position(0, 1)) is friendly


def test_arrival_at_friendly_destination_no_cooldown():
    rook = make_piece(0, 0)
    friendly = make_piece(0, 1, kind=Kind.BISHOP)
    board, arbiter, resolver = setup([rook, friendly])
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)
    assert not arbiter.is_piece_on_cooldown(rook)


# --- airborne enemy ---

def test_arrival_at_airborne_enemy_captures_mover():
    rook = make_piece(0, 0)
    enemy = make_piece(0, 1, color=Color.BLACK)
    board, arbiter, resolver = setup([rook, enemy])
    arbiter.start_jump(enemy)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)
    assert rook.state == PieceState.CAPTURED
    assert board.piece_at(Position(0, 0)) is None


def test_arrival_at_airborne_enemy_lands_jumper():
    rook = make_piece(0, 0)
    enemy = make_piece(0, 1, color=Color.BLACK)
    board, arbiter, resolver = setup([rook, enemy])
    arbiter.start_jump(enemy)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)
    assert board.piece_at(Position(0, 1)) is enemy
    assert enemy.state == PieceState.IDLE


def test_arrival_at_airborne_king_captures_mover():
    rook = make_piece(0, 0)
    king = make_piece(0, 1, kind=Kind.KING, color=Color.BLACK)
    board, arbiter, resolver = setup([rook, king])
    arbiter.start_jump(king)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)
    assert rook.state == PieceState.CAPTURED
    assert board.piece_at(Position(0, 1)) is king


# --- landing on an occupied cell ---

def test_landing_on_enemy_captures_enemy():
    rook = make_piece(0, 0)
    enemy = make_piece(0, 0, color=Color.BLACK)
    board, arbiter, resolver = setup([rook])
    arbiter.start_jump(rook)
    board.remove_piece(Position(0, 0))
    board.add_piece(enemy)
    arbiter.advance_time(1000, resolver)
    assert enemy.state == PieceState.CAPTURED
    assert board.piece_at(Position(0, 0)) is rook


def test_landing_on_king_sets_game_over():
    rook = make_piece(0, 0)
    king = make_piece(0, 0, kind=Kind.KING, color=Color.BLACK)
    board, arbiter, resolver = setup([rook])
    arbiter.start_jump(rook)
    board.remove_piece(Position(0, 0))
    board.add_piece(king)
    assert arbiter.advance_time(1000, resolver)


# --- friendly airborne cells clear after landing ---

def test_friendly_airborne_cells_empty_after_landing():
    rook = make_piece(0, 0)
    board, arbiter, resolver = setup([rook])
    arbiter.start_jump(rook)
    board.remove_piece(Position(0, 0))
    arbiter.advance_time(1000, resolver)
    assert arbiter.friendly_airborne_cells(Color.WHITE) == set()


# --- arrival order ---

def test_earlier_arrival_wins_contested_destination():
    rook1 = make_piece(0, 0)
    rook2 = make_piece(0, 3, color=Color.BLACK)
    board, arbiter, resolver = setup([rook1, rook2])
    arbiter.start_motion(rook1, Position(0, 1))  # arrives at 1000ms
    arbiter.start_motion(rook2, Position(0, 1))  # arrives at 2000ms
    arbiter.advance_time(2000, resolver)
    assert board.piece_at(Position(0, 1)) is rook2
    assert rook1.state == PieceState.CAPTURED
