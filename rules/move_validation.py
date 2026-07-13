from dataclasses import dataclass


@dataclass(frozen=True)
class MoveValidation:
    is_valid: bool
    reason: str

    OK                          = "ok"
    OUTSIDE_BOARD               = "outside_board"
    EMPTY_SOURCE                = "empty_source"
    FRIENDLY_DESTINATION        = "friendly_destination"
    FRIENDLY_AIRBORNE_DESTINATION = "friendly_airborne_destination"
    ILLEGAL_PIECE_MOVE          = "illegal_piece_move"
