from __future__ import annotations
from typing import Protocol
from model.piece import Piece, PieceState
from model.position import Position
from realtime.motion import Motion
from realtime.jump import Jump


class ArrivalHandler(Protocol):
    """Callback contract for resolving due events. Implemented by engine.arrival_resolver.ArrivalResolver.
    Kept as a Protocol here so this module never needs to import the engine layer."""
    def resolve_arrival(self, motion: Motion) -> bool: ...
    def resolve_landing(self, jump: Jump) -> bool: ...


class RealTimeArbiter:
    """Pure timing scheduler: tracks active motions, jumps, the game clock, and cooldowns.
    Holds no reference to the Board — resolving what an arrival/landing does to the board
    is delegated to an injected ArrivalResolver (engine layer) on every advance_time call."""

    def __init__(self):
        self._clock     = 0
        self._motions:   list[Motion] = []
        self._jumps:     list[Jump]   = []
        self._cooldowns: dict[str, int] = {}  # piece.id → ready_time

    def is_piece_moving(self, piece: Piece) -> bool:
        """Returns True if the given piece already has an active motion."""
        return any(m.piece == piece for m in self._motions)

    def is_piece_airborne(self, piece: Piece) -> bool:
        """Returns True if the given piece is currently airborne."""
        return any(j.piece == piece for j in self._jumps)

    def is_piece_airborne_at(self, cell: Position) -> bool:
        """Returns True if an airborne piece occupies the given cell."""
        return any(j.cell == cell for j in self._jumps)

    def is_piece_on_cooldown(self, piece: Piece) -> bool:
        """Returns True if the piece is resting after a move or jump."""
        return self._cooldowns.get(piece.id, 0) > self._clock

    def cooldown_remaining(self, piece: Piece) -> int:
        """Returns remaining cooldown in ms, or 0 if ready."""
        return max(0, self._cooldowns.get(piece.id, 0) - self._clock)

    def airborne_pieces(self) -> list[Piece]:
        """Returns all pieces currently airborne."""
        return [j.piece for j in self._jumps]

    def friendly_airborne_cells(self, color) -> set[Position]:
        """Returns the cells occupied by airborne pieces of the given color."""
        return {j.cell for j in self._jumps if j.piece.color == color}

    def moving_origins(self) -> set[Position]:
        """Returns the origin positions of all pieces currently in motion."""
        return {m.origin for m in self._motions}

    def airborne_jump_at(self, cell: Position, color) -> Jump | None:
        """Returns the pending jump of an enemy of the given color occupying cell, or None.
        Used by the ArrivalResolver to detect an arriving motion landing on an airborne piece."""
        return next((j for j in self._jumps if j.cell == cell and j.piece.color != color), None)

    def start_motion(self, piece: Piece, destination: Position) -> None:
        """Registers a new motion for a validated move. Marks the piece as moving."""
        piece.state = PieceState.MOVING
        self._motions.append(Motion(piece, piece.cell, destination, self._clock))

    def start_jump(self, piece: Piece) -> None:
        """Registers a new jump for the piece at its current square. Marks it as airborne.
        The caller (GameEngine) is responsible for removing the piece from the Board."""
        piece.state = PieceState.AIRBORNE
        self._jumps.append(Jump(piece, piece.cell, self._clock))

    def cancel_jump(self, jump: Jump) -> None:
        """Removes a pending jump before its land_time — used when it is resolved mid-air
        (e.g. the jumper lands early because it captured an arriving attacker)."""
        self._jumps = [j for j in self._jumps if j is not jump]

    def set_cooldown(self, piece: Piece, ready_time: int) -> None:
        """Records when the given piece will be ready to act again."""
        self._cooldowns[piece.id] = ready_time

    def _next_event_time(self, target_time: int) -> int:
        """Returns the earliest arrival or landing time up to target_time."""
        t = target_time
        for m in self._motions:
            if m.arrival_time < t:
                t = m.arrival_time
        for j in self._jumps:
            if j.land_time < t:
                t = j.land_time
        return t

    def _pop_due_events(self) -> tuple[list[Motion], list[Jump]]:
        """Removes and returns the motions/jumps due at the current clock time,
        motions sorted by arrival order (earliest first)."""
        due_motions   = sorted(
            [m for m in self._motions if m.arrival_time <= self._clock],
            key=lambda m: m.arrival_time
        )
        self._motions = [m for m in self._motions if m.arrival_time > self._clock]

        due_landings  = [j for j in self._jumps if j.land_time <= self._clock]
        self._jumps   = [j for j in self._jumps if j.land_time  > self._clock]

        return due_motions, due_landings

    def advance_time(self, ms: int, resolver: ArrivalHandler) -> bool:
        """Advances the clock by ms, handing each due motion/jump to the resolver as it becomes due.
        Returns True if a victory condition was met."""
        target_time = self._clock + ms
        victory     = False

        while self._clock < target_time:
            self._clock = self._next_event_time(target_time)
            due_motions, due_jumps = self._pop_due_events()

            for motion in due_motions:
                if resolver.resolve_arrival(motion):
                    victory = True

            for jump in due_jumps:
                if resolver.resolve_landing(jump):
                    victory = True

        return victory
