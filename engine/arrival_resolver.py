from __future__ import annotations
from typing import TYPE_CHECKING, Callable
from model.board import Board
from model.piece import Piece, PieceState, Kind
from model.position import Position
from realtime.motion import Motion, COOLDOWN_MS
from realtime.jump import Jump, JUMP_COOLDOWN_MS
from rules.piece_rules import PieceRules
from engine.score_keeper import ScoreKeeper
from engine.move_log import MoveEntry, to_notation
from engine.events import MoveResolvedEvent, JumpResolvedEvent

if TYPE_CHECKING:
    from realtime.real_time_arbiter import RealTimeArbiter

SettlementCallback = Callable[[object], None]


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
        self._move_log:    list[MoveEntry] = []
        self._winner:      str | None = None  # "w" or "b"
        self._callbacks:   list[SettlementCallback] = []
        self._arrival_origins: dict[str, Position] = {}  # piece.id → origin of last completed motion

    def add_settlement_listener(self, callback: SettlementCallback) -> None:
        """Registers a callback invoked with a MoveResolvedEvent or JumpResolvedEvent
        after every arrival/landing. Additive, backward-compatible."""
        self._callbacks.append(callback)

    def _publish(self, event: object) -> None:
        for cb in self._callbacks:
            cb(event)

    def _is_victory(self, piece: Piece) -> bool:
        """Returns True if capturing this piece ends the game."""
        return piece.kind == Kind.KING

    @property
    def move_log(self) -> list[MoveEntry]:
        return self._move_log

    @property
    def winner(self) -> str | None:
        return self._winner

    def _record_capture(self, capturing_color, captured_piece: Piece) -> bool:
        """Updates score and winner for a capture. Returns True if it was a king capture."""
        victory = self._is_victory(captured_piece)
        self._score_keeper.record_capture(capturing_color, captured_piece.kind)
        if victory:
            self._winner = capturing_color.value
        return victory

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
        motion.piece.state = PieceState.CAPTURED
        victory = self._record_capture(airborne_enemy.piece.color, motion.piece)
        self._arbiter.cancel_jump(airborne_enemy)
        airborne_enemy.piece.state = PieceState.IDLE
        self._board.add_piece(airborne_enemy.piece)
        self._arbiter.set_cooldown(airborne_enemy.piece, airborne_enemy.ready_time, JUMP_COOLDOWN_MS)
        clock = self._arbiter.current_time_ms
        cell  = airborne_enemy.piece.cell
        self._move_log.append(MoveEntry(
            airborne_enemy.piece.color.value,
            to_notation(airborne_enemy.piece.kind.value,
                        cell.row, cell.col, cell.row, cell.col, True),
            clock,
        ))
        self._publish(JumpResolvedEvent(
            pos=(cell.row, cell.col),
            piece_kind=airborne_enemy.piece.kind.value,
            piece_color=airborne_enemy.piece.color.value,
            captured_piece_kind=motion.piece.kind.value,
            time_ms=clock,
        ))
        return victory

    def _handle_destination(self, motion: Motion) -> bool:
        if self._board.piece_at(motion.origin) is not motion.piece:
            return False
        self._board.remove_piece(motion.origin)
        occupant = self._board.piece_at(motion.destination)
        victory  = False
        if occupant is not None:
            if occupant.color == motion.piece.color:
                motion.piece.state = PieceState.IDLE
                self._board.add_piece(motion.piece)
                return False
            victory = self._record_capture(motion.piece.color, occupant)
            occupant.state = PieceState.CAPTURED
            self._board.remove_piece(motion.destination)
        motion.piece.state = PieceState.IDLE
        motion.piece.cell  = motion.destination
        self._board.add_piece(motion.piece)
        self._arrival_origins[motion.piece.id] = motion.origin
        self._arbiter.set_cooldown(motion.piece, motion.ready_time, COOLDOWN_MS)
        was_pawn = motion.piece.kind == Kind.PAWN
        self._rules[motion.piece.kind].on_arrival(motion.piece, self._board.rows)
        if was_pawn and motion.piece.kind == Kind.QUEEN:
            self._score_keeper.record_promotion(motion.piece.color)
        clock = self._arbiter.current_time_ms
        self._move_log.append(MoveEntry(
            motion.piece.color.value,
            to_notation(motion.piece.kind.value, motion.origin.row, motion.origin.col,
                        motion.destination.row, motion.destination.col, occupant is not None),
            clock,
        ))
        self._publish(MoveResolvedEvent(
            src=(motion.origin.row, motion.origin.col),
            dst=(motion.destination.row, motion.destination.col),
            piece_kind=motion.piece.kind.value,
            piece_color=motion.piece.color.value,
            captured_piece_kind=occupant.kind.value if occupant is not None else None,
            time_ms=clock,
        ))
        return victory

    def resolve_landing(self, jump: Jump) -> bool:
        if jump.piece.state == PieceState.CAPTURED:
            return False
        occupant = self._board.piece_at(jump.cell)
        if occupant is not None and occupant.color == jump.piece.color:
            origin = self._arrival_origins.get(occupant.id, occupant.cell)
            self._board.remove_piece(jump.cell)
            occupant.state = PieceState.IDLE
            occupant.cell  = origin
            self._board.add_piece(occupant)
            occupant = None
        jump.piece.state = PieceState.IDLE
        victory = False
        if occupant is not None:
            victory = self._record_capture(jump.piece.color, occupant)
            occupant.state = PieceState.CAPTURED
            self._board.remove_piece(jump.cell)
        self._board.add_piece(jump.piece)
        self._arbiter.set_cooldown(jump.piece, jump.ready_time, JUMP_COOLDOWN_MS)
        clock = self._arbiter.current_time_ms
        self._move_log.append(MoveEntry(
            jump.piece.color.value,
            to_notation(jump.piece.kind.value, jump.cell.row, jump.cell.col,
                        jump.cell.row, jump.cell.col, occupant is not None),
            clock,
        ))
        self._publish(JumpResolvedEvent(
            pos=(jump.cell.row, jump.cell.col),
            piece_kind=jump.piece.kind.value,
            piece_color=jump.piece.color.value,
            captured_piece_kind=occupant.kind.value if occupant is not None else None,
            time_ms=clock,
        ))
        return victory
