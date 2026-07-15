from __future__ import annotations
from model.piece import Kind, Color

PIECE_VALUES: dict[Kind, int] = {
    Kind.PAWN:   1,
    Kind.KNIGHT: 3,
    Kind.BISHOP: 3,
    Kind.ROOK:   5,
    Kind.QUEEN:  9,
    Kind.KING:   0,  # capturing the king ends the game; not scored as a point value
}
PROMOTION_BONUS = 9


class ScoreKeeper:
    """Tracks each side's score: piece values for captures, plus a bonus for promoting to
    Queen (awarded even without a capture). Pure bookkeeping — no Board/timing knowledge."""

    def __init__(self):
        self._scores: dict[Color, int] = {Color.WHITE: 0, Color.BLACK: 0}

    def score(self, color: Color) -> int:
        """Returns the current score for the given side."""
        return self._scores[color]

    def record_capture(self, capturing_color: Color, captured_kind: Kind) -> None:
        """Awards the capturing side points for the piece kind it captured."""
        self._scores[capturing_color] += PIECE_VALUES[captured_kind]

    def record_promotion(self, color: Color) -> None:
        """Awards the promotion-to-Queen bonus to the given side."""
        self._scores[color] += PROMOTION_BONUS
