"""ELO rating calculator (standard FIDE formula)."""
from __future__ import annotations

# K-factor determines how much a single game score affects the rating.
# Standard value for most casual/intermediate chess pools is 32.
K = 32


def expected(rating_a: int, rating_b: int) -> float:
    """Calculates the expected winning probability of Player A against Player B.
    
    Formula: E_A = 1 / (1 + 10 ^ ((Rating_B - Rating_A) / 400))
    """
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


def updated_ratings(winner_elo: int, loser_elo: int) -> tuple[int, int]:
    """Calculates and returns (new_winner_elo, new_loser_elo) after a decisive match."""
    e_win = expected(winner_elo, loser_elo)
    
    # Calculate rating changes based on the difference between actual score (1/0) and expected score
    new_winner = round(winner_elo + K * (1 - e_win))
    new_loser  = round(loser_elo  + K * (0 - (1 - e_win)))
    
    return new_winner, new_loser