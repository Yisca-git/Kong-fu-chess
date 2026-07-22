"""Typed events emitted by NetworkClient to its caller."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class WaitingEvent:
    elo: str

@dataclass(frozen=True)
class MatchedEvent:
    color:      str
    opponent:   str
    opp_elo:    str
    reconnected: bool

@dataclass(frozen=True)
class TimeoutEvent:
    pass

@dataclass(frozen=True)
class EloUpdateEvent:
    new_elo: int

@dataclass(frozen=True)
class OpponentDisconnectedEvent:
    pass

@dataclass(frozen=True)
class OpponentForfeitedEvent:
    pass

@dataclass(frozen=True)
class ErrorEvent:
    message: str

NetworkEvent = (WaitingEvent | MatchedEvent | TimeoutEvent |
                EloUpdateEvent | OpponentDisconnectedEvent |
                OpponentForfeitedEvent | ErrorEvent)
