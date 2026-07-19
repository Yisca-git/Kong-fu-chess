from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from realtime.jump import Jump
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


def _trigger_game_over(engine, board):
    """Captures the black king to set game_over via real engine logic."""
    rook = make_piece(0, 0)
    king = make_piece(0, 1, kind=Kind.KING, color=Color.BLACK)
    board.add_piece(rook)
    board.add_piece(king)
    engine.request_move(Position(0, 0), Position(0, 1))
    engine.advance_time(1000)


def test_rejects_move_when_game_over():
    rook = make_piece(0, 4)
    board, engine = setup([rook])
    _trigger_game_over(engine, board)
    result = engine.request_move(Position(0, 1), Position(0, 4))
    assert not result.is_accepted
    assert result.reason == "game_over"


def test_rejects_jump_when_game_over():
    rook = make_piece(0, 4)
    board, engine = setup([rook])
    _trigger_game_over(engine, board)
    result = engine.request_jump(Position(0, 1))
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


# --- player names ---

def test_snapshot_default_player_names():
    rook = make_piece(0, 0)
    board, engine = setup([rook])
    snapshot = engine.snapshot()
    assert snapshot.white_name == "White"
    assert snapshot.black_name == "Black"


def test_snapshot_custom_player_names():
    rook = make_piece(0, 0)
    board = Board(8, 8)
    board.add_piece(rook)
    arbiter  = RealTimeArbiter()
    resolver = ArrivalResolver(board, RULES_BY_KIND, arbiter, ScoreKeeper())
    engine   = GameEngine(board, RuleEngine(), arbiter, resolver, ScoreKeeper(),
                          white_name="Alice", black_name="Bob")
    snapshot = engine.snapshot()
    assert snapshot.white_name == "Alice"
    assert snapshot.black_name == "Bob"


# --- empty source ---

def test_rejects_move_from_empty_source():
    board, engine = setup([])
    result = engine.request_move(Position(3, 3), Position(3, 4))
    assert not result.is_accepted
    assert result.reason == "empty_source"


def test_rejects_jump_from_empty_source():
    board, engine = setup([])
    result = engine.request_jump(Position(3, 3))
    assert not result.is_accepted
    assert result.reason == "empty_source"


# --- in_bounds ---

def test_in_bounds_returns_true_for_valid_position():
    board, engine = setup([])
    assert engine.in_bounds(Position(0, 0))
    assert engine.in_bounds(Position(7, 7))


# --- set_cursor / set_rejection / set_selected do not raise ---

def test_set_cursor_does_not_raise():
    board, engine = setup([])
    engine.set_cursor(100, 200)
    engine.set_cursor(None, None)


def test_set_rejection_does_not_raise():
    board, engine = setup([])
    engine.set_rejection("some_reason")
    engine.set_rejection(None)


def test_set_selected_does_not_raise():
    board, engine = setup([])
    engine.set_selected(Position(0, 0))
    engine.set_selected(None)


# --- pawn promotion via engine ---

def test_pawn_promotion_via_arrival():
    """A white pawn arriving at row 0 must be promoted to Queen."""
    pawn = make_piece(1, 0, kind=Kind.PAWN)
    board, engine = setup([pawn])
    engine.request_move(Position(1, 0), Position(0, 0))
    engine.advance_time(1000)
    assert pawn.kind == Kind.QUEEN


def test_pawn_promotion_awards_score():
    """Promotion must add the promotion bonus to the promoting side's score."""
    pawn = make_piece(1, 0, kind=Kind.PAWN)
    board = Board(8, 8)
    board.add_piece(pawn)
    arbiter   = RealTimeArbiter()
    sk        = ScoreKeeper()
    resolver  = ArrivalResolver(board, RULES_BY_KIND, arbiter, sk)
    engine    = GameEngine(board, RuleEngine(), arbiter, resolver, sk)
    engine.request_move(Position(1, 0), Position(0, 0))
    engine.advance_time(1000)
    assert sk.score(Color.WHITE) == 9


# --- resolve_landing on already-captured piece ---

def test_resolve_landing_on_captured_piece_is_noop():
    """If a jumping piece is captured before it lands, resolve_landing must be a no-op."""
    from realtime.jump import Jump
    from model.piece import PieceState
    rook = make_piece(0, 0)
    board = Board(8, 8)
    arbiter  = RealTimeArbiter()
    resolver = ArrivalResolver(board, RULES_BY_KIND, arbiter, ScoreKeeper())
    rook.state = PieceState.CAPTURED
    jump = Jump(rook, cell=Position(0, 0), start_time=0)
    result = resolver.resolve_landing(jump)
    assert result is False
