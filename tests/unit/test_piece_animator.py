from view.piece_animator import PieceAnimator, FRAME_DURATION_MS


def test_frame_index_starts_at_zero():
    animator = PieceAnimator()
    assert animator.frame_index("p1", "idle", now_ms=0, frame_count=5) == 0


def test_frame_index_advances_over_time():
    animator = PieceAnimator()
    animator.frame_index("p1", "idle", now_ms=0, frame_count=5)
    index = animator.frame_index("p1", "idle", now_ms=FRAME_DURATION_MS * 2, frame_count=5)
    assert index == 2


def test_frame_index_loops_back_to_zero():
    animator = PieceAnimator()
    animator.frame_index("p1", "idle", now_ms=0, frame_count=5)
    index = animator.frame_index("p1", "idle", now_ms=FRAME_DURATION_MS * 5, frame_count=5)
    assert index == 0


def test_state_change_resets_animation_to_frame_zero():
    animator = PieceAnimator()
    animator.frame_index("p1", "idle", now_ms=0, frame_count=5)
    animator.frame_index("p1", "idle", now_ms=FRAME_DURATION_MS * 3, frame_count=5)
    # switching state at the same instant should restart the cycle at frame 0
    index = animator.frame_index("p1", "moving", now_ms=FRAME_DURATION_MS * 3, frame_count=5)
    assert index == 0


def test_different_pieces_animate_independently():
    animator = PieceAnimator()
    animator.frame_index("p1", "idle", now_ms=0, frame_count=5)
    animator.frame_index("p2", "idle", now_ms=FRAME_DURATION_MS * 2, frame_count=5)
    assert animator.frame_index("p1", "idle", now_ms=FRAME_DURATION_MS * 2, frame_count=5) == 2
    assert animator.frame_index("p2", "idle", now_ms=FRAME_DURATION_MS * 2, frame_count=5) == 0


def test_folder_state_mapping():
    animator = PieceAnimator()
    assert animator.folder_state_for("idle") == "idle"
    assert animator.folder_state_for("moving") == "move"
    assert animator.folder_state_for("airborne") == "jump"


def test_folder_state_defaults_to_idle_for_unknown_state():
    animator = PieceAnimator()
    assert animator.folder_state_for("captured") == "idle"
