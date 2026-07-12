from board import Board
from piece import Piece, PieceState, Kind
from position import Position
from motion import Motion
from jump import Jump
from piece_rules import PieceRules


class RealTimeArbiter:
    def __init__(self, board, rules):
        self._board     = board
        self._rules     = rules
        self._clock     = 0
        self._motions   = []
        self._jumps     = []
        self._cooldowns = {}

    def is_piece_moving(self, piece):
        return any(m.piece == piece for m in self._motions)

    def is_piece_airborne(self, piece):
        return any(j.piece == piece for j in self._jumps)

    def is_piece_on_cooldown(self, piece):
        return self._cooldowns.get(id(piece), 0) > self._clock

    def cooldown_remaining(self, piece):
        return max(0, self._cooldowns.get(id(piece), 0) - self._clock)

    def airborne_pieces(self):
        return [j.piece for j in self._jumps]

    def moving_origins(self):
        return {m.origin for m in self._motions}

    def start_motion(self, piece, destination):
        piece.state = PieceState.MOVING
        self._motions.append(Motion(piece, piece.cell, destination, self._clock))

    def start_jump(self, piece):
        self._board.remove_piece(piece.cell)
        piece.state = PieceState.AIRBORNE
        self._jumps.append(Jump(piece, piece.cell, self._clock))

    def _next_event_time(self, target_time):
        t = target_time
        for m in self._motions:
            if m.arrival_time < t:
                t = m.arrival_time
        for j in self._jumps:
            if j.land_time < t:
                t = j.land_time
        return t

    def _process_due_events(self):
        king_captured = False
        due_motions   = [m for m in self._motions if m.arrival_time <= self._clock]
        self._motions = [m for m in self._motions if m.arrival_time  > self._clock]
        for motion in reversed(due_motions):
            if self._resolve_arrival(motion):
                king_captured = True
        due_landings = [j for j in self._jumps if j.land_time <= self._clock]
        self._jumps  = [j for j in self._jumps if j.land_time  > self._clock]
        for jump in due_landings:
            self._resolve_landing(jump)
        return king_captured

    def advance_time(self, ms):
        target_time   = self._clock + ms
        king_captured = False
        while self._clock < target_time:
            self._clock = self._next_event_time(target_time)
            if self._process_due_events():
                king_captured = True
        return king_captured

    def _resolve_arrival(self, motion):
        king_captured = False
        airborne_enemy = next(
            (j for j in self._jumps
             if j.cell == motion.destination and j.piece.color != motion.piece.color),
            None,
        )
        if airborne_enemy is not None:
            self._board.remove_piece(motion.origin)
            if motion.piece.kind == Kind.KING:
                king_captured = True
            motion.piece.state = PieceState.CAPTURED
            self._jumps = [j for j in self._jumps if j is not airborne_enemy]
            airborne_enemy.piece.state = PieceState.IDLE
            self._board.add_piece(airborne_enemy.piece)
            self._cooldowns[id(airborne_enemy.piece)] = airborne_enemy.ready_time
            return king_captured
        self._board.remove_piece(motion.origin)
        occupant = self._board.piece_at(motion.destination)
        if occupant is not None:
            if occupant.kind == Kind.KING:
                king_captured = True
            occupant.state = PieceState.CAPTURED
            self._board.remove_piece(motion.destination)
        motion.piece.state = PieceState.IDLE
        motion.piece.cell  = motion.destination
        self._board.add_piece(motion.piece)
        self._cooldowns[id(motion.piece)] = motion.ready_time
        self._rules[motion.piece.kind].on_arrival(motion.piece, self._board.rows)
        return king_captured

    def _resolve_landing(self, jump):
        if jump.piece.state == PieceState.CAPTURED:
            return
        jump.piece.state = PieceState.IDLE
        if self._board.is_empty(jump.cell):
            self._board.add_piece(jump.piece)
            self._cooldowns[id(jump.piece)] = jump.ready_time
        else:
            jump.piece.state = PieceState.CAPTURED
