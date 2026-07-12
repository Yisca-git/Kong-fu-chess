from dataclasses import dataclass


@dataclass(frozen=True)
class MoveValidation:
    is_valid: bool
    reason: str
