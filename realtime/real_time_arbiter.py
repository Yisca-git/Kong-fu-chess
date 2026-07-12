from model.board import Board
from model.piece import Piece, PieceState, Kind
from model.position import Position
from realtime.motion import Motion
from rules.rules_registry import RULES_BY_KIND


class RealTimeArbiter:
    def __init__(self, board: Board):
        self._board   = board
        self._clock   = 0
        self._motions: list[Motion] = []

    def is_piece_moving(self, piece: Piece) -> bool:
        """Returns True if the given piece already has an active motion."""
        return any(m.piece is piece for m in self._motions)

    def moving_origins(self) -> set[Position]:
        """Returns the origin positions of all pieces currently in motion."""
        return {m.origin for m in self._motions}

    def start_motion(self, piece: Piece, destination: Position) -> None:
        """Registers a new motion for a validated move. Marks the piece as moving."""
        piece.state = PieceState.MOVING
        self._motions.append(Motion(piece, piece.cell, destination, self._clock))

    def advance_time(self, ms: int) -> bool:
        """Advances the clock by ms and resolves all arrivals. Returns True if a king was captured."""
        target_time   = self._clock + ms
        king_captured = False

        while self._clock < target_time:
            next_arrival = min(
                (m.arrival_time for m in self._motions),
                default=target_time,
            )
            self._clock = min(next_arrival, target_time)

            due = [m for m in self._motions if m.arrival_time <= self._clock]
            self._motions = [m for m in self._motions if m.arrival_time > self._clock]

            for motion in due:
                if self._resolve_arrival(motion):
                    king_captured = True

        return king_captured

    def _resolve_arrival(self, motion: Motion) -> bool:
        """Resolves a single arrival atomically. Returns True if a king was captured."""
        king_captured = False

        self._board.remove_piece(motion.origin)

        occupant = self._board.piece_at(motion.destination)
        if occupant is not None:
            if occupant.kind == Kind.KING:
                king_captured = True
            self._board.remove_piece(motion.destination)

        motion.piece.state = PieceState.IDLE
        motion.piece.cell  = motion.destination
        self._board.add_piece(motion.piece)

        RULES_BY_KIND[motion.piece.kind].on_arrival(motion.piece, self._board.rows)

        return king_captured
