from dataclasses import dataclass


@dataclass(frozen=True)
class MoveResult:
    is_accepted: bool
    reason: str
