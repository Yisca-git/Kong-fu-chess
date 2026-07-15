from model.piece import Piece, Color, Kind, PieceState
from model.position import Position
from realtime.real_time_arbiter import RealTimeArbiter
from realtime.motion import Motion
from realtime.jump import Jump


def make_piece(row, col, kind=Kind.ROOK, color=Color.WHITE):
    return Piece(id=f"{color.value}{kind.value}", color=color, kind=kind, cell=Position(row, col))


class _SpyResolver:
    """Records which motions/jumps became due, without touching any board."""
    def __init__(self, victory_on=None):
        self.arrivals: list[Motion] = []
        self.landings: list[Jump]   = []
        self._victory_on = victory_on

    def resolve_arrival(self, motion: Motion) -> bool:
        self.arrivals.append(motion)
        return motion is self._victory_on

    def resolve_landing(self, jump: Jump) -> bool:
        self.landings.append(jump)
        return jump is self._victory_on


# --- timing: due events reach the resolver at the right time ---

def test_motion_not_due_before_arrival_time():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(999, resolver)
    assert resolver.arrivals == []


def test_motion_due_exactly_at_arrival_time():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.start_motion(rook, Position(0, 1))
    arbiter.advance_time(1000, resolver)
    assert [m.piece for m in resolver.arrivals] == [rook]


def test_diagonal_motion_uses_chebyshev_distance():
    bishop = make_piece(0, 0, kind=Kind.BISHOP)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.start_motion(bishop, Position(3, 3))
    arbiter.advance_time(2999, resolver)
    assert resolver.arrivals == []
    arbiter.advance_time(1, resolver)
    assert len(resolver.arrivals) == 1


def test_jump_lands_after_jump_duration():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.start_jump(rook)
    arbiter.advance_time(999, resolver)
    assert resolver.landings == []
    arbiter.advance_time(1, resolver)
    assert [j.piece for j in resolver.landings] == [rook]


def test_earlier_arrival_resolved_before_later_one():
    rook1 = make_piece(0, 0)
    rook2 = make_piece(0, 3, color=Color.BLACK)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.start_motion(rook1, Position(0, 1))  # arrives at 1000ms
    arbiter.start_motion(rook2, Position(0, 1))  # arrives at 2000ms
    arbiter.advance_time(2000, resolver)
    assert [m.piece for m in resolver.arrivals] == [rook1, rook2]


# --- victory propagation ---

def test_advance_time_returns_true_when_resolver_reports_victory():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    arbiter.start_motion(rook, Position(0, 1))
    motion = arbiter._motions[0]
    resolver = _SpyResolver(victory_on=motion)
    assert arbiter.advance_time(1000, resolver)


def test_advance_time_returns_false_without_victory():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.start_motion(rook, Position(0, 1))
    assert not arbiter.advance_time(1000, resolver)


# --- piece/motion state flags ---

def test_start_motion_marks_piece_moving():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    arbiter.start_motion(rook, Position(0, 1))
    assert rook.state == PieceState.MOVING
    assert arbiter.is_piece_moving(rook)


def test_moving_origins_returns_source_cell():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    arbiter.start_motion(rook, Position(0, 1))
    assert arbiter.moving_origins() == {Position(0, 0)}


def test_start_jump_marks_piece_airborne():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    arbiter.start_jump(rook)
    assert rook.state == PieceState.AIRBORNE
    assert arbiter.is_piece_airborne(rook)
    assert arbiter.is_piece_airborne_at(Position(0, 0))


def test_friendly_airborne_cells_returns_jumped_cell():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    arbiter.start_jump(rook)
    assert arbiter.friendly_airborne_cells(Color.WHITE) == {Position(0, 0)}


def test_friendly_airborne_cells_excludes_enemy():
    enemy = make_piece(0, 1, color=Color.BLACK)
    arbiter = RealTimeArbiter()
    arbiter.start_jump(enemy)
    assert arbiter.friendly_airborne_cells(Color.WHITE) == set()


def test_airborne_jump_at_finds_enemy_jump():
    enemy = make_piece(0, 1, color=Color.BLACK)
    arbiter = RealTimeArbiter()
    arbiter.start_jump(enemy)
    jump = arbiter.airborne_jump_at(Position(0, 1), Color.WHITE)
    assert jump is not None and jump.piece is enemy


def test_airborne_jump_at_ignores_friendly_jump():
    friendly = make_piece(0, 1, color=Color.WHITE)
    arbiter = RealTimeArbiter()
    arbiter.start_jump(friendly)
    assert arbiter.airborne_jump_at(Position(0, 1), Color.WHITE) is None


def test_cancel_jump_removes_pending_jump():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    arbiter.start_jump(rook)
    jump = arbiter.airborne_jump_at(Position(0, 0), Color.BLACK)
    arbiter.cancel_jump(jump)
    assert not arbiter.is_piece_airborne(rook)


# --- cooldown bookkeeping ---

def test_set_cooldown_then_is_on_cooldown():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    arbiter.set_cooldown(rook, 1000, 1000)
    assert arbiter.is_piece_on_cooldown(rook)


def test_cooldown_expires_after_clock_passes_ready_time():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.set_cooldown(rook, 500, 500)
    arbiter.advance_time(500, resolver)
    assert not arbiter.is_piece_on_cooldown(rook)


def test_cooldown_remaining_decreases_over_time():
    rook = make_piece(0, 0)
    arbiter = RealTimeArbiter()
    resolver = _SpyResolver()
    arbiter.set_cooldown(rook, 1000, 1000)
    arbiter.advance_time(400, resolver)
    assert arbiter.cooldown_remaining(rook) == 600


def test_jump_cooldown_shorter_than_move_cooldown():
    from realtime.motion import COOLDOWN_MS
    from realtime.jump import JUMP_COOLDOWN_MS
    assert JUMP_COOLDOWN_MS < COOLDOWN_MS

