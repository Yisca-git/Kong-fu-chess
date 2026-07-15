from __future__ import annotations
from typing import TYPE_CHECKING
from model.board import Board
from model.piece import Piece, PieceState, Kind
from realtime.motion import Motion
from realtime.jump import Jump
from rules.piece_rules import PieceRules

if TYPE_CHECKING:
    from realtime.real_time_arbiter import RealTimeArbiter


class ArrivalResolver:
    """Applies motion arrivals and jump landings to the Board: captures, blocking,
    promotion (via on_arrival), and victory detection.

    RealTimeArbiter only tracks timing (motions, jumps, the clock, cooldowns) and holds
    no reference to the Board — this class is the sole owner of board mutations on arrival,
    wired together by GameEngine."""

    def __init__(self, board: Board, rules: dict[Kind, PieceRules], arbiter: RealTimeArbiter):
        self._board   = board
        self._rules   = rules
        self._arbiter = arbiter

    def _is_victory(self, piece: Piece) -> bool:
        """Returns True if capturing this piece ends the game. Override to change win condition."""
        return piece.kind == Kind.KING

    def resolve_arrival(self, motion: Motion) -> bool:
        """Resolves a single arrival. Returns True if a victory condition was met."""
        if self._handle_airborne_enemy(motion):
            return True
        return self._handle_destination(motion)

    def _handle_airborne_enemy(self, motion: Motion) -> bool:
        """Handles the case where an airborne enemy is on the destination. Returns True if a victory condition was met."""
        airborne_enemy = self._arbiter.airborne_jump_at(motion.destination, motion.piece.color)
        if airborne_enemy is None:
            return False
        self._board.remove_piece(motion.origin)
        victory = self._is_victory(airborne_enemy.piece)
        motion.piece.state = PieceState.CAPTURED
        self._arbiter.cancel_jump(airborne_enemy)
        airborne_enemy.piece.state = PieceState.IDLE
        self._board.add_piece(airborne_enemy.piece)
        self._arbiter.set_cooldown(airborne_enemy.piece, airborne_enemy.ready_time)
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
        self._arbiter.set_cooldown(motion.piece, motion.ready_time)
        self._rules[motion.piece.kind].on_arrival(motion.piece, self._board.rows)
        return victory

    def resolve_landing(self, jump: Jump) -> bool:
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
        self._arbiter.set_cooldown(jump.piece, jump.ready_time)
        return victory
