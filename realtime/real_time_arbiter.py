from model.board import Board
from model.piece import Piece, PieceState, Kind
from model.position import Position
from realtime.motion import Motion

from realtime.jump import Jump
from rules.rules_registry import RULES_BY_KIND


class RealTimeArbiter:
    def __init__(self, board: Board):
        self._board   = board
        self._clock   = 0
        self._motions: list[Motion] = []
        self._jumps:   list[Jump]   = []

    def is_piece_moving(self, piece: Piece) -> bool:
        """Returns True if the given piece already has an active motion."""
        return any(m.piece is piece for m in self._motions)

    def is_piece_airborne(self, piece: Piece) -> bool:
        """Returns True if the given piece is currently airborne."""
        return any(j.piece is piece for j in self._jumps)

    def airborne_pieces(self) -> list[Piece]:
        """Returns all pieces currently airborne."""
        return [j.piece for j in self._jumps]

    def moving_origins(self) -> set[Position]:
        """Returns the origin positions of all pieces currently in motion."""
        return {m.origin for m in self._motions}

    def start_motion(self, piece: Piece, destination: Position) -> None:
        """Registers a new motion for a validated move. Marks the piece as moving."""
        piece.state = PieceState.MOVING
        self._motions.append(Motion(piece, piece.cell, destination, self._clock))

    def start_jump(self, piece: Piece) -> None:
        """Makes a piece airborne at its current square. Removes it from the board until landing."""
        self._board.remove_piece(piece.cell)
        piece.state = PieceState.AIRBORNE
        self._jumps.append(Jump(piece, piece.cell, self._clock))

    def advance_time(self, ms: int) -> bool:
        """Advances the clock by ms and resolves all arrivals and landings. Returns True if a king was captured."""
        target_time   = self._clock + ms
        king_captured = False

        while self._clock < target_time:
            next_event = target_time
            for m in self._motions:
                if m.arrival_time < next_event:
                    next_event = m.arrival_time
            for j in self._jumps:
                if j.land_time < next_event:
                    next_event = j.land_time
            self._clock = min(next_event, target_time)

            due_motions = [m for m in self._motions if m.arrival_time <= self._clock]
            self._motions = [m for m in self._motions if m.arrival_time > self._clock]

            due_landings = [j for j in self._jumps if j.land_time <= self._clock]
            self._jumps = [j for j in self._jumps if j.land_time > self._clock]

            for motion in due_motions:
                if self._resolve_arrival(motion):
                    king_captured = True

            for jump in due_landings:
                self._resolve_landing(jump)

        return king_captured

    def _resolve_arrival(self, motion: Motion) -> bool:
        """Resolves a single arrival. If destination has an airborne piece, the jumper captures the attacker.
        Returns True if a king was captured."""
        king_captured = False

        # Check if an enemy piece is airborne over the destination
        airborne_at_dest = next(
            (j for j in self._jumps
             if j.cell == motion.destination and j.piece.color != motion.piece.color),
            None,
        )
        if airborne_at_dest is not None:
            # Jumper captures the attacker — remove attacker from motion, don't land it
            self._board.remove_piece(motion.origin)
            if motion.piece.kind == Kind.KING:
                king_captured = True
            return king_captured

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

    def _resolve_landing(self, jump: Jump) -> None:
        """Places an airborne piece back on its square after the jump window expires."""
        jump.piece.state = PieceState.IDLE
        if self._board.is_empty(jump.cell):
            self._board.add_piece(jump.piece)
        else:
            # Square was occupied while airborne — piece is displaced (captured)
            jump.piece.state = PieceState.CAPTURED
