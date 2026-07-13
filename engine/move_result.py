from dataclasses import dataclass


@dataclass(frozen=True)
class MoveResult:
    is_accepted: bool
    reason: str

    OK                     = "ok"
    GAME_OVER              = "game_over"
    EMPTY_SOURCE           = "empty_source"
    PIECE_ALREADY_MOVING   = "piece_already_moving"
    PIECE_ON_COOLDOWN      = "piece_on_cooldown"
    PIECE_ALREADY_AIRBORNE = "piece_already_airborne"
    FRIENDLY_DESTINATION   = "friendly_destination"
