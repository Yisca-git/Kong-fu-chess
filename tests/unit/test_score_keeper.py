from model.piece import Color, Kind
from engine.score_keeper import ScoreKeeper


def test_initial_score_is_zero():
    sk = ScoreKeeper()
    assert sk.score(Color.WHITE) == 0
    assert sk.score(Color.BLACK) == 0


def test_capture_pawn_adds_one():
    sk = ScoreKeeper()
    sk.record_capture(Color.WHITE, Kind.PAWN)
    assert sk.score(Color.WHITE) == 1


def test_capture_knight_adds_three():
    sk = ScoreKeeper()
    sk.record_capture(Color.BLACK, Kind.KNIGHT)
    assert sk.score(Color.BLACK) == 3


def test_capture_bishop_adds_three():
    sk = ScoreKeeper()
    sk.record_capture(Color.WHITE, Kind.BISHOP)
    assert sk.score(Color.WHITE) == 3


def test_capture_rook_adds_five():
    sk = ScoreKeeper()
    sk.record_capture(Color.WHITE, Kind.ROOK)
    assert sk.score(Color.WHITE) == 5


def test_capture_queen_adds_nine():
    sk = ScoreKeeper()
    sk.record_capture(Color.BLACK, Kind.QUEEN)
    assert sk.score(Color.BLACK) == 9


def test_capture_king_adds_zero():
    sk = ScoreKeeper()
    sk.record_capture(Color.WHITE, Kind.KING)
    assert sk.score(Color.WHITE) == 0


def test_promotion_adds_nine():
    sk = ScoreKeeper()
    sk.record_promotion(Color.WHITE)
    assert sk.score(Color.WHITE) == 9


def test_captures_accumulate():
    sk = ScoreKeeper()
    sk.record_capture(Color.WHITE, Kind.PAWN)
    sk.record_capture(Color.WHITE, Kind.ROOK)
    assert sk.score(Color.WHITE) == 6


def test_scores_are_independent_per_color():
    sk = ScoreKeeper()
    sk.record_capture(Color.WHITE, Kind.QUEEN)
    sk.record_capture(Color.BLACK, Kind.PAWN)
    assert sk.score(Color.WHITE) == 9
    assert sk.score(Color.BLACK) == 1


def test_promotion_and_capture_accumulate():
    sk = ScoreKeeper()
    sk.record_capture(Color.WHITE, Kind.PAWN)
    sk.record_promotion(Color.WHITE)
    assert sk.score(Color.WHITE) == 10
