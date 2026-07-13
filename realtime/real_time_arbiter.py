from model.board import Board
from model.piece import Piece, PieceState, Kind
from model.position import Position
from realtime.motion import Motion
from realtime.jump import Jump
from rules.piece_rules import PieceRules


class RealTimeArbiter:
    def __init__(self, board: Board, rules: dict[Kind, PieceRules]):
        self._board     = board
        self._rules     = rules
        self._clock     = 0
        self._motions:   list[Motion] = []
        self._jumps:     list[Jump]   = []
        self._cooldowns: dict[int, int] = {}  # piece id → ready_time

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
        return self._cooldowns.get(id(piece), 0) > self._clock

    def cooldown_remaining(self, piece: Piece) -> int:
        """Returns remaining cooldown in ms, or 0 if ready."""
        return max(0, self._cooldowns.get(id(piece), 0) - self._clock)

    def airborne_pieces(self) -> list[Piece]:
        """Returns all pieces currently airborne."""
        return [j.piece for j in self._jumps]

    def friendly_airborne_cells(self, color) -> set[Position]:
        """Returns the cells occupied by airborne pieces of the given color."""
        return {j.cell for j in self._jumps if j.piece.color == color}

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

    def _process_due_events(self) -> bool:
        """Resolves all motions and jumps due at the current clock. Returns True if a victory condition was met."""
        victory = False

        due_motions   = sorted(
            [m for m in self._motions if m.arrival_time <= self._clock],
            key=lambda m: m.arrival_time
        )
        self._motions = [m for m in self._motions if m.arrival_time > self._clock]

        due_landings  = [j for j in self._jumps if j.land_time <= self._clock]
        self._jumps   = [j for j in self._jumps if j.land_time  > self._clock]

        for motion in due_motions:
            if self._resolve_arrival(motion):
                victory = True

        for jump in due_landings:
            if self._resolve_landing(jump):
                victory = True

        return victory

    def advance_time(self, ms: int) -> bool:
        """Advances the clock by ms and resolves all arrivals and landings. Returns True if a victory condition was met."""
        target_time = self._clock + ms
        victory     = False

        while self._clock < target_time:
            self._clock = self._next_event_time(target_time)
            if self._process_due_events():
                victory = True

        return victory

    def _is_victory(self, piece: Piece) -> bool:
        """Returns True if capturing this piece ends the game. Override to change win condition."""
        return piece.kind == Kind.KING

    def _handle_airborne_enemy(self, motion: Motion) -> bool:
        """Handles the case where an airborne enemy is on the destination. Returns True if a victory condition was met."""
        airborne_enemy = next(
            (j for j in self._jumps
             if j.cell == motion.destination and j.piece.color != motion.piece.color),
            None,
        )
        if airborne_enemy is None:
            return False
        self._board.remove_piece(motion.origin)
        victory = self._is_victory(airborne_enemy.piece)
        motion.piece.state = PieceState.CAPTURED
        self._jumps = [j for j in self._jumps if j is not airborne_enemy]
        airborne_enemy.piece.state = PieceState.IDLE
        self._board.add_piece(airborne_enemy.piece)
        self._cooldowns[id(airborne_enemy.piece)] = airborne_enemy.ready_time
        return victory

    def _handle_destination(self, motion: Motion) -> bool:
        """Handles arrival at destination: blocks if friendly, captures if enemy, or moves to empty cell. Returns True if a victory condition was met."""
        self._board.remove_piece(motion.origin)
        occupant = self._board.piece_at(motion.destination)
        if occupant is not None:
            if occupant.color == motion.piece.color:
                motion.piece.state = PieceState.IDLE
                self._board.add_piece(motion.piece)
                return False
            victory = self._is_victory(occupant)
            occupant.state = PieceState.CAPTURED
            self._board.remove_piece(motion.destination)
        else:
            victory = False
        motion.piece.state = PieceState.IDLE
        motion.piece.cell  = motion.destination
        self._board.add_piece(motion.piece)
        self._cooldowns[id(motion.piece)] = motion.ready_time
        self._rules[motion.piece.kind].on_arrival(motion.piece, self._board.rows)
        return victory

    def _resolve_arrival(self, motion: Motion) -> bool:
        """Resolves a single arrival. Returns True if a victory condition was met."""
        if self._handle_airborne_enemy(motion):
            return True
        return self._handle_destination(motion)

    def _resolve_landing(self, jump: Jump) -> bool:
        """Places an airborne piece back on its square after the jump window expires. Returns True if a victory condition was met."""
        if jump.piece.state == PieceState.CAPTURED:
            return False
        jump.piece.state = PieceState.IDLE
        occupant = self._board.piece_at(jump.cell)
        if occupant is not None:
            victory = self._is_victory(occupant)
            occupant.state = PieceState.CAPTURED
            self._board.remove_piece(jump.cell)
        else:
            victory = False
        self._board.add_piece(jump.piece)
        self._cooldowns[id(jump.piece)] = jump.ready_time
        return victory
