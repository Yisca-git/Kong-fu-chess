from view.events.event_bus import EventBus
from view.events.events import MoveResolvedEvent, JumpResolvedEvent
from view.events.observers.score_observer import ScoreObserver
from view.events.observers.moves_log_observer import MovesLogObserver


# ── EventBus ──────────────────────────────────────────────────────────────────

def test_event_bus_delivers_to_subscriber():
    bus      = EventBus()
    received = []
    bus.subscribe(MoveResolvedEvent, received.append)
    event = MoveResolvedEvent((6,4),(4,4),"P","w",None,1000)
    bus.publish(event)
    assert received == [event]


def test_event_bus_delivers_to_multiple_subscribers():
    bus = EventBus()
    a, b = [], []
    bus.subscribe(MoveResolvedEvent, a.append)
    bus.subscribe(MoveResolvedEvent, b.append)
    event = MoveResolvedEvent((6,4),(4,4),"P","w",None,1000)
    bus.publish(event)
    assert a == [event] and b == [event]


def test_event_bus_does_not_deliver_wrong_type():
    bus      = EventBus()
    received = []
    bus.subscribe(MoveResolvedEvent, received.append)
    bus.publish(JumpResolvedEvent((3,3),"N","b",None,500))
    assert received == []


def test_event_bus_no_subscribers_does_not_raise():
    bus = EventBus()
    bus.publish(MoveResolvedEvent((0,0),(1,1),"R","b",None,0))


# ── ScoreObserver ─────────────────────────────────────────────────────────────

def test_score_observer_starts_at_zero():
    obs = ScoreObserver()
    assert obs.score == {"w": 0, "b": 0}


def test_score_observer_adds_pawn_value():
    obs = ScoreObserver()
    obs.on_move_resolved(MoveResolvedEvent((6,4),(5,5),"P","w","P",1000))
    assert obs.score["w"] == 1


def test_score_observer_adds_queen_value():
    obs = ScoreObserver()
    obs.on_move_resolved(MoveResolvedEvent((0,3),(1,3),"Q","b","Q",2000))
    assert obs.score["b"] == 9


def test_score_observer_no_capture_adds_nothing():
    obs = ScoreObserver()
    obs.on_move_resolved(MoveResolvedEvent((6,4),(4,4),"P","w",None,1000))
    assert obs.score["w"] == 0


def test_score_observer_jump_capture():
    obs = ScoreObserver()
    obs.on_jump_resolved(JumpResolvedEvent((3,3),"N","w","R",500))
    assert obs.score["w"] == 5


def test_score_observer_accumulates():
    obs = ScoreObserver()
    obs.on_move_resolved(MoveResolvedEvent((0,0),(1,0),"R","w","P",100))
    obs.on_move_resolved(MoveResolvedEvent((0,1),(1,1),"N","w","B",200))
    assert obs.score["w"] == 4


# ── MovesLogObserver ──────────────────────────────────────────────────────────

def test_moves_log_starts_empty():
    obs = MovesLogObserver()
    assert obs.entries == []


def test_moves_log_appends_on_move():
    obs = MovesLogObserver()
    obs.on_move_resolved(MoveResolvedEvent((6,4),(4,4),"P","w",None,1000))
    assert len(obs.entries) == 1
    assert obs.entries[0].color == "w"
    assert obs.entries[0].time_ms == 1000


def test_moves_log_appends_on_jump():
    obs = MovesLogObserver()
    obs.on_jump_resolved(JumpResolvedEvent((3,3),"N","b",None,500))
    assert len(obs.entries) == 1
    assert obs.entries[0].color == "b"


def test_moves_log_capture_notation_has_x():
    obs = MovesLogObserver()
    obs.on_move_resolved(MoveResolvedEvent((6,4),(5,5),"P","w","P",1000))
    assert "X" in obs.entries[0].notation


def test_moves_log_no_capture_notation_has_no_x():
    obs = MovesLogObserver()
    obs.on_move_resolved(MoveResolvedEvent((6,4),(4,4),"P","w",None,1000))
    assert "X" not in obs.entries[0].notation


def test_moves_log_accumulates_multiple_entries():
    obs = MovesLogObserver()
    obs.on_move_resolved(MoveResolvedEvent((6,4),(4,4),"P","w",None,1000))
    obs.on_move_resolved(MoveResolvedEvent((1,4),(3,4),"P","b",None,1200))
    assert len(obs.entries) == 2


# ── ScoreObserver — king capture ──────────────────────────────────────────────

def test_score_observer_king_capture_adds_no_points():
    """Capturing a king ends the game but must not add score (K is not in PIECE_VALUES)."""
    obs = ScoreObserver()
    obs.on_move_resolved(MoveResolvedEvent((0,4),(1,4),"R","w","K",1000))
    assert obs.score["w"] == 0


def test_score_observer_king_capture_via_jump_adds_no_points():
    obs = ScoreObserver()
    obs.on_jump_resolved(JumpResolvedEvent((0,4),"N","w","K",500))
    assert obs.score["w"] == 0
