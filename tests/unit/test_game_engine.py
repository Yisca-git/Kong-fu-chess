from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rule_engine import RuleEngine
from rules.rules_registry import RULES_BY_KIND
from engine.game_engine import GameEngine
from engine.arrival_resolver import ArrivalResolver
from engine.score_keeper import ScoreKeeper


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def setup(pieces):
    board = Board(8, 8)
    for p in pieces:
        board.add_piece(p)
    arbiter  = RealTimeArbiter()
    resolver = ArrivalResolver(board, RULES_BY_KIND, arbiter, ScoreKeeper())
    engine   = GameEngine(board, RuleEngine(), arbiter, resolver, ScoreKeeper())
    return board, engine


def test_rejects_move_when_game_over():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.game_over = True
    result = engine.request_move(Position(0, 0), Position(0, 4))
    assert not result.is_accepted
    assert result.reason == "game_over"


def test_rejects_jump_when_game_over():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.game_over = True
    result = engine.request_jump(Position(0, 0))
    assert not result.is_accepted
    assert result.reason == "game_over"


def test_rejects_jump_when_already_airborne():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.request_jump(Position(0, 0))
    result = engine.request_jump(Position(0, 0))
    assert not result.is_accepted
    assert result.reason == "piece_already_airborne"


def test_rejects_jump_when_piece_on_cooldown():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.request_jump(Position(0, 0))
    engine.advance_time(1000)  # landing, cooldown starts
    result = engine.request_jump(Position(0, 0))
    assert not result.is_accepted
    assert result.reason == "piece_on_cooldown"


def test_rejects_move_when_piece_already_moving():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.request_move(Position(0, 0), Position(0, 4))
    result = engine.request_move(Position(0, 0), Position(0, 1))
    assert not result.is_accepted
    assert result.reason == "piece_already_moving"


def test_rejects_move_when_piece_on_cooldown():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.request_move(Position(0, 0), Position(0, 1))
    engine.advance_time(1000)  # arrival, cooldown starts
    result = engine.request_move(Position(0, 1), Position(0, 2))
    assert not result.is_accepted
    assert result.reason == "piece_on_cooldown"


def test_accepts_move_after_cooldown_expires():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.request_move(Position(0, 0), Position(0, 1))
    engine.advance_time(2000)  # arrival + cooldown
    result = engine.request_move(Position(0, 1), Position(0, 2))
    assert result.is_accepted

def test_rejects_invalid_move():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    result = engine.request_move(Position(0, 0), Position(1, 1))
    assert not result.is_accepted
    assert result.reason == "illegal_piece_move"


def test_accepts_valid_move():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    result = engine.request_move(Position(0, 0), Position(0, 4))
    assert result.is_accepted
    assert result.reason == "ok"


def test_advance_time_moves_piece():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    engine.request_move(Position(0, 0), Position(0, 4))
    engine.advance_time(4000)
    assert board.piece_at(Position(0, 4)) is rook


def test_king_capture_sets_game_over():
    rook = make_piece(0, 0)
    king = make_piece(0, 1, kind=Kind.KING, color=Color.BLACK)
    board, engine = setup([rook, king])
    engine.request_move(Position(0, 0), Position(0, 1))
    engine.advance_time(1000)
    assert engine.game_over


def test_snapshot_reflects_current_state():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    snapshot = engine.snapshot()
    assert len(snapshot.pieces) == 1
    assert snapshot.pieces[0].row == 0
    assert snapshot.pieces[0].col == 0
