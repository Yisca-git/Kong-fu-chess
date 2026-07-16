from __future__ import annotations
from collections import defaultdict
from typing import Callable, Type, TypeVar

E = TypeVar("E")
Handler = Callable[[E], None]


class EventBus:
    """Minimal synchronous pub/sub. Publishing is O(subscribers) and happens
    outside the render call stack so a slow observer never blocks frame timing."""

    def __init__(self) -> None:
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def subscribe(self, event_type: Type[E], handler: Handler) -> None:
        self._handlers[event_type].append(handler)

    def publish(self, event: object) -> None:
        for handler in self._handlers[type(event)]:
            handler(event)
