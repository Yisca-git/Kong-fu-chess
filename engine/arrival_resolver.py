from __future__ import annotations
from typing import TYPE_CHECKING
from model.board import Board
from model.piece import Piece, PieceState, Kind
from realtime.motion import Motion, COOLDOWN_MS
from realtime.jump import Jump, JUMP_COOLDOWN_MS
from rules.piece_rules import PieceRules
from engine.score_keeper import ScoreKeeper
from engine.move_log import MoveEntry, to_notation

if TYPE_CHECKING:
    from realtime.real_time_arbiter import RealTimeArbiter


class ArrivalResolver:
    """Applies motion arrivals and jump landings to the Board: captures, blocking,
    promotion (via on_arrival), victory detection, and score bookkeeping.

    RealTimeArbiter only tracks timing (motions, jumps, the clock, cooldowns) and holds
    no reference to the Board — this class is the sole owner of board mutations on arrival,
    wired together by GameEngine."""

    def __init__(self, board: Board, rules: dict[Kind, PieceRules], arbiter: RealTimeArbiter,
                 score_keeper: ScoreKeeper):
        self._board        = board
        self._rules        = rules
        self._arbiter      = arbiter
        self._score_keeper = score_keeper
        self.move_log:     list[MoveEntry] = []
        self.winner:       str | None = None  # "w" or "b"

    def _is_victory(self, piece: Piece) -> bool:
        """Returns True if capturing this piece ends the game."""
        return piece.kind == Kind.KING

    def resolve_arrival(self, motion: Motion) -> bool:
        """Resolves a single arrival. Returns True if a victory condition was met."""
        if self._handle_airborne_enemy(motion):
            return True
        return self._handle_destination(motion)

    def _handle_airborne_enemy(self, motion: Motion) -> bool:
        airborne_enemy = self._arbiter.airborne_jump_at(motion.destination, motion.piece.color)
        if airborne_enemy is None:
            return False
        self._board.remove_piece(motion.origin)
        victory = self._is_victory(airborne_enemy.piece)
        motion.piece.state = PieceState.CAPTURED
        self._score_keeper.record_capture(airborne_enemy.piece.color, motion.piece.kind)
        if victory:
            self.winner = airborne_enemy.piece.color.value
        self._arbiter.cancel_jump(airborne_enemy)
        airborne_enemy.piece.state = PieceState.IDLE
        self._board.add_piece(airborne_enemy.piece)
        self._arbiter.set_cooldown(airborne_enemy.piece, airborne_enemy.ready_time, JUMP_COOLDOWN_MS)
        return victory

    def _handle_destination(self, motion: Motion) -> bool:
        self._board.remove_piece(motion.origin)
        occupant = self._board.piece_at(motion.destination)
        if occupant is not None:
            if occupant.color == motion.piece.color:
                motion.piece.state = PieceState.IDLE
                self._board.add_piece(motion.piece)
                return False
            victory = self._is_victory(occupant)
            occupant.state = PieceState.CAPTURED
            self._score_keeper.record_capture(motion.piece.color, occupant.kind)
            self._board.remove_piece(motion.destination)
            if victory:
                self.winner = motion.piece.color.value
        else:
            victory = False
        motion.piece.state = PieceState.IDLE
        motion.piece.cell  = motion.destination
        self._board.add_piece(motion.piece)
        self._arbiter.set_cooldown(motion.piece, motion.ready_time, COOLDOWN_MS)
        was_pawn = motion.piece.kind == Kind.PAWN
        self._rules[motion.piece.kind].on_arrival(motion.piece, self._board.rows)
        if was_pawn and motion.piece.kind == Kind.QUEEN:
            self._score_keeper.record_promotion(motion.piece.color)
        self.move_log.append(MoveEntry(
            motion.piece.color.value,
            to_notation(motion.piece.kind.value, motion.origin.row, motion.origin.col,
                        motion.destination.row, motion.destination.col, occupant is not None),
            self._arbiter._clock,
        ))
        return victory

    def resolve_landing(self, jump: Jump) -> bool:
        if jump.piece.state == PieceState.CAPTURED:
            return False
        jump.piece.state = PieceState.IDLE
        occupant = self._board.piece_at(jump.cell)
        if occupant is not None:
            victory = self._is_victory(occupant)
            occupant.state = PieceState.CAPTURED
            self._score_keeper.record_capture(jump.piece.color, occupant.kind)
            self._board.remove_piece(jump.cell)
            if victory:
                self.winner = jump.piece.color.value
        else:
            victory = False
        self._board.add_piece(jump.piece)
        self._arbiter.set_cooldown(jump.piece, jump.ready_time, JUMP_COOLDOWN_MS)
        self.move_log.append(MoveEntry(
            jump.piece.color.value,
            to_notation(jump.piece.kind.value, jump.cell.row, jump.cell.col,
                        jump.cell.row, jump.cell.col, occupant is not None),
            self._arbiter._clock,
        ))
        return victory
