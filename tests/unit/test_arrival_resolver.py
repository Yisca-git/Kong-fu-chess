from model.board import Board
from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from rules.rules_registry import RULES_BY_KIND
from engine.arrival_resolver import ArrivalResolver
from engine.score_keeper import ScoreKeeper


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


def setup(pieces):
    board    = Board(8, 8)
    for p in pieces:
        board.add_piece(p)
    arbiter  = RealTimeArbiter()
    resolver = ArrivalResolver(board, RULES_BY_KIND, arbiter, ScoreKeeper())
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


# --- jump cancelled when attacker arrives on same tick ---

def test_attacker_arriving_same_tick_as_jump_land_does_not_double_resolve():
    """Regression: when a motion and a jump land on the same tick, cancel_jump must
    prevent resolve_landing from running on the already-settled jump."""
    rook  = make_piece(0, 0)                          # attacker, moves 1 square -> arrives at 1000ms
    enemy = make_piece(0, 1, color=Color.BLACK)       # jumper, jump duration = 1000ms -> lands at 1000ms
    board, arbiter, resolver = setup([rook, enemy])
    arbiter.start_jump(enemy)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(rook, Position(0, 1))        # both events due at exactly 1000ms
    arbiter.advance_time(1000, resolver)              # must not raise ValueError
    assert rook.state == PieceState.CAPTURED
    assert board.piece_at(Position(0, 1)) is enemy
    assert enemy.state == PieceState.IDLE


# --- landing on friendly piece ---

def test_landing_on_friendly_returns_friendly_to_origin():
    """If a friendly piece arrived at the landing cell while the jumper was airborne,
    the friendly piece returns to its origin and the jumper lands normally."""
    white_rook1 = make_piece(0, 1)                        # friendly, moves into the jump cell
    white_rook2 = make_piece(0, 0)                        # jumps from (0,0)
    board, arbiter, resolver = setup([white_rook1, white_rook2])
    arbiter.start_jump(white_rook2)
    board.remove_piece(Position(0, 0))
    arbiter.start_motion(white_rook1, Position(0, 0))     # friendly moves into the now-empty cell
    arbiter.advance_time(2000, resolver)
    assert white_rook2.state == PieceState.IDLE
    assert board.piece_at(Position(0, 0)) is white_rook2  # jumper lands
    assert board.piece_at(Position(0, 1)) is white_rook1  # friendly back at origin


def test_landing_on_enemy_after_enemy_moved_in_captures_enemy():
    """If an enemy piece moves into the landing cell while the jumper is airborne,
    the jumper lands and captures the enemy normally."""
    white_rook = make_piece(0, 1)                         # enemy, moves into the jump cell
    black_rook = make_piece(0, 0, color=Color.BLACK)      # jumps from (0,0)
    board, arbiter, resolver = setup([white_rook, black_rook])
    arbiter.start_jump(black_rook)
    board.remove_piece(Position(0, 0))
    arbiter.start_motion(white_rook, Position(0, 0))      # enemy moves into the now-empty cell
    arbiter.advance_time(2000, resolver)
    assert white_rook.state == PieceState.CAPTURED
    assert board.piece_at(Position(0, 0)) is black_rook


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


# --- airborne enemy: event publishing ---

def test_airborne_enemy_capture_publishes_jump_event():
    """When a moving piece is captured by an airborne jumper, a JumpResolvedEvent
    must be published so score and move-log are updated."""
    rook  = make_piece(0, 0)
    enemy = make_piece(0, 1, color=Color.BLACK)
    board, arbiter, resolver = setup([rook, enemy])
    events = []
    resolver.add_settlement_listener(events.append)

    arbiter.start_jump(enemy)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)

    from view.events.events import JumpResolvedEvent
    jump_events = [e for e in events if isinstance(e, JumpResolvedEvent)]
    assert len(jump_events) == 1
    assert jump_events[0].captured_piece_kind == rook.kind.value
    assert jump_events[0].piece_color == enemy.color.value


def test_airborne_enemy_capture_has_capture_flag_in_log():
    """The move-log entry for an airborne capture must have is_capture=True (X in notation)."""
    rook  = make_piece(0, 0)
    enemy = make_piece(0, 1, color=Color.BLACK)
    board, arbiter, resolver = setup([rook, enemy])

    arbiter.start_jump(enemy)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)

    assert any("X" in e.notation for e in resolver.move_log)


def test_airborne_enemy_capture_increments_score():
    """ScoreObserver must receive the JumpResolvedEvent and add the captured piece's value."""
    from view.events.event_bus import EventBus
    from view.events.events import JumpResolvedEvent
    from view.events.observers.score_observer import ScoreObserver

    rook  = make_piece(0, 0, kind=Kind.ROOK)          # value=5, captured by enemy
    enemy = make_piece(0, 1, color=Color.BLACK, kind=Kind.KNIGHT)
    board, arbiter, resolver = setup([rook, enemy])

    bus   = EventBus()
    score = ScoreObserver()
    bus.subscribe(JumpResolvedEvent, score.on_jump_resolved)
    resolver.add_settlement_listener(bus.publish)

    arbiter.start_jump(enemy)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)

    assert score.score["b"] == 5  # rook value


def test_airborne_king_capture_does_not_add_score():
    """Capturing a king via airborne must not add score (game ends, K has no value)."""
    from view.events.event_bus import EventBus
    from view.events.events import JumpResolvedEvent
    from view.events.observers.score_observer import ScoreObserver

    king  = make_piece(0, 0, kind=Kind.KING)
    enemy = make_piece(0, 1, color=Color.BLACK, kind=Kind.KNIGHT)
    board, arbiter, resolver = setup([king, enemy])

    bus   = EventBus()
    score = ScoreObserver()
    bus.subscribe(JumpResolvedEvent, score.on_jump_resolved)
    resolver.add_settlement_listener(bus.publish)

    arbiter.start_jump(enemy)
    board.remove_piece(Position(0, 1))
    arbiter.start_motion(king, Position(0, 1))
    arbiter.advance_time(1000, resolver)

    assert score.score["b"] == 0
