"""ELO rating calculator (standard FIDE formula, K=32)."""
from __future__ import annotations

K = 32


def expected(rating_a: int, rating_b: int) -> float:
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def updated_ratings(winner_elo: int, loser_elo: int) -> tuple[int, int]:
    """Returns (new_winner_elo, new_loser_elo)."""
    e_win = expected(winner_elo, loser_elo)
    new_winner = round(winner_elo + K * (1 - e_win))
    new_loser  = round(loser_elo  + K * (0 - (1 - e_win)))
    return new_winner, new_loser
