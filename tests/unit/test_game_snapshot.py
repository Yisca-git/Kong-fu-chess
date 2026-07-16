from engine.game_snapshot import GameSnapshot, PieceSnapshot


def _empty_snapshot(**kwargs) -> GameSnapshot:
    defaults = dict(pieces=(), game_over=False, rows=8, cols=8)
    defaults.update(kwargs)
    return GameSnapshot(**defaults)


# --- default field values ---

def test_default_white_name():
    s = _empty_snapshot()
    assert s.white_name == "White"


def test_default_black_name():
    s = _empty_snapshot()
    assert s.black_name == "Black"


def test_default_scores_are_zero():
    s = _empty_snapshot()
    assert s.white_score == 0
    assert s.black_score == 0


def test_default_winner_is_none():
    s = _empty_snapshot()
    assert s.winner is None


def test_default_selected_is_none():
    s = _empty_snapshot()
    assert s.selected_row is None
    assert s.selected_col is None


# --- from_pieces ---

def test_from_pieces_default_names():
    s = GameSnapshot.from_pieces([], False, 8, 8)
    assert s.white_name == "White"
    assert s.black_name == "Black"


def test_from_pieces_custom_names():
    s = GameSnapshot.from_pieces([], False, 8, 8, white_name="Alice", black_name="Bob")
    assert s.white_name == "Alice"
    assert s.black_name == "Bob"


def test_from_pieces_scores_passed_through():
    s = GameSnapshot.from_pieces([], False, 8, 8, white_score=9, black_score=3)
    assert s.white_score == 9
    assert s.black_score == 3


def test_from_pieces_winner_passed_through():
    s = GameSnapshot.from_pieces([], True, 8, 8, winner="w")
    assert s.winner == "w"


def test_from_pieces_empty_move_log():
    s = GameSnapshot.from_pieces([], False, 8, 8)
    assert s.move_log == ()


# --- PieceSnapshot defaults ---

def test_piece_snapshot_default_motion_progress():
    p = PieceSnapshot(id="wR", color="w", kind="R", row=0, col=0)
    assert p.motion_progress == 1.0


def test_piece_snapshot_default_state_is_idle():
    p = PieceSnapshot(id="wR", color="w", kind="R", row=0, col=0)
    assert p.state == "idle"


def test_piece_snapshot_default_cooldown_is_zero():
    p = PieceSnapshot(id="wR", color="w", kind="R", row=0, col=0)
    assert p.cooldown_progress == 0.0


def test_piece_snapshot_default_dest_is_none():
    p = PieceSnapshot(id="wR", color="w", kind="R", row=0, col=0)
    assert p.dest_row is None
    assert p.dest_col is None
