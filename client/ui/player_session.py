"""PlayerSession: wires NetworkClient (network) + RenderLoop (UI) + input."""
from __future__ import annotations
import cv2

from engine.game_snapshot import GameSnapshot, PieceSnapshot
from view.config import PANEL_W, CELL_SIZE
from view.events.observers.sound_observer import SoundObserver
from input.board_mapper import pixel_to_position
from client.network.network_client import NetworkClient
from client.network.events import (NetworkEvent, WaitingEvent, MatchedEvent, TimeoutEvent,
                                   EloUpdateEvent, OpponentDisconnectedEvent,
                                   OpponentForfeitedEvent, ErrorEvent)
from client.ui.render_loop import RenderLoop

MATCH_TIMEOUT = 70


class PlayerSession(RenderLoop):
    """Composition root for a playing client: owns the NetworkClient and handles input."""

    def __init__(self, username: str) -> None:
        super().__init__(window_name=f"Kong-Fu-Chess — {username}")
        self._username       = username
        self._cell_size      = CELL_SIZE
        self._selected:      tuple[int, int] | None = None
        self._prev_log_len:  int = 0
        self._prev_piece_ids: set[str] = set()
        self._sound_obs      = SoundObserver()
        self._net            = NetworkClient(
            username=username,
            on_snapshot=self._on_snapshot_received,
            on_event=self._on_event,
        )

    # ------------------------------------------------------------------ RenderLoop hooks

    def _ready_event(self):
        return self._net.matched

    def _start_ws_thread(self) -> None:
        self._net.start()

    def _on_tick(self, snap: GameSnapshot) -> None:
        sound = self._detect_sound_event(snap)
        if sound:
            self._sound_obs.play_sound(sound)
        self._prev_log_len   = len(snap.move_log)
        self._prev_piece_ids = {p.id for p in snap.pieces}

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        board_x = x - PANEL_W
        if board_x < 0 or self._snapshot is None or self._net.color is None:
            return
        if self._net.opponent_countdown is not None:
            return
        try:
            pos = pixel_to_position(board_x, y, self._cell_size)
        except (ValueError, ZeroDivisionError):
            return
        if not (0 <= pos.row < self._snapshot.rows and 0 <= pos.col < self._snapshot.cols):
            return
        color = self._net.color

        if event == cv2.EVENT_RBUTTONDOWN:
            piece = self._piece_at(pos.row, pos.col)
            if piece and piece.color == color[0]:
                self._net.send_jump(piece.color, piece.kind, pos.row, pos.col)
            self._selected = None

        elif event == cv2.EVENT_LBUTTONDOWN:
            if self._selected is None:
                piece = self._piece_at(pos.row, pos.col)
                if piece and piece.color == color[0]:
                    self._selected = (pos.row, pos.col)
            else:
                sr, sc = self._selected
                piece = self._piece_at(sr, sc)
                if piece:
                    self._net.send_move(piece.color, piece.kind, sr, sc, pos.row, pos.col)
                self._selected = None

    # ------------------------------------------------------------------ private

    def _on_snapshot_received(self, snap: GameSnapshot) -> None:
        self._snapshot = snap

    def _on_event(self, event: NetworkEvent) -> None:
        match event:
            case WaitingEvent(elo=elo):
                print(f"[client] In matchmaking queue... (ELO: {elo})")
            case MatchedEvent(color=color, opponent=opp, opp_elo=opp_elo, reconnected=True):
                print(f"[client] Reconnected as {color}")
            case MatchedEvent(color=color, opponent=opp, opp_elo=opp_elo):
                print(f"[client] Matched! You are {color} vs {opp} (ELO {opp_elo})")
            case TimeoutEvent():
                print("[client] Matchmaking timed out. No opponent found.")
            case EloUpdateEvent(new_elo=elo):
                print(f"[client] Your new ELO: {elo}")
            case OpponentDisconnectedEvent():
                print("[client] Opponent disconnected — waiting for reconnect...")
            case OpponentForfeitedEvent():
                print("[client] Opponent forfeited. You win!")
            case ErrorEvent(message=msg):
                print(f"[client] Server error: {msg}")

    def _piece_at(self, row: int, col: int) -> PieceSnapshot | None:
        if self._snapshot is None:
            return None
        return next((p for p in self._snapshot.pieces
                     if p.row == row and p.col == col and p.state != "captured"), None)

    def _detect_sound_event(self, snap: GameSnapshot) -> str | None:
        if len(snap.move_log) <= self._prev_log_len:
            return None
        cur_ids = {p.id for p in snap.pieces}
        if self._prev_piece_ids - cur_ids:
            return "capture.wav"
        prev_airborne = {p.id for p in (self._snapshot.pieces if self._snapshot else [])
                         if p.state == "airborne"}
        new_airborne = {p.id for p in snap.pieces if p.state == "airborne"}
        return "jump.wav" if new_airborne - prev_airborne else "move.wav"

    def _on_window_closed(self) -> None:
        if not self._user_closed:
            return
        if self._snapshot and self._snapshot.game_over:
            return
        try:
            self._net.send_disconnect()
        except RuntimeError:
            pass

    # ------------------------------------------------------------------ run

    def run(self) -> None:
        self._start_ws_thread()
        self._net.matched.wait(timeout=MATCH_TIMEOUT)
        if self._net.timed_out or self._net.color is None:
            return
        self._run_loop()
