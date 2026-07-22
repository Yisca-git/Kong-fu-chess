"""NetworkClient: interactive player client over WebSocket."""
from __future__ import annotations
import asyncio
import json
import threading

import cv2
import websockets

from engine.game_snapshot import GameSnapshot, PieceSnapshot
from view.config import PANEL_W, CELL_SIZE
from view.events.observers.sound_observer import SoundObserver
from input.board_mapper import pixel_to_position
from client.protocol.codec import parse_snapshot, encode_move, encode_jump
from client.ui.render_loop import RenderLoop
from client.config import SERVER_URI


class NetworkClient(RenderLoop):
    """Bridges the OpenCV window with the WebSocket server."""

    def __init__(self, username: str = "guest") -> None:
        super().__init__()
        self._username    = username
        self._cell_size   = CELL_SIZE
        self._prev_log_len: int = 0
        self._prev_piece_ids: set[str] = set()
        self._color:      str | None = None
        self._game_id:    int | None = None
        self._selected:   tuple[int, int] | None = None
        self._ws          = None
        self._loop:       asyncio.AbstractEventLoop | None = None
        self._matched     = threading.Event()
        self._timed_out   = False
        self._sound_obs   = SoundObserver()

    def _ready_event(self) -> threading.Event:
        return self._matched

    # ------------------------------------------------------------------ sound

    def _on_tick(self, snap: GameSnapshot) -> None:
        self._tick_sounds(snap)

    def _tick_sounds(self, snap: GameSnapshot) -> None:
        new_log_len = len(snap.move_log)
        if new_log_len > self._prev_log_len:
            cur_ids  = {p.id for p in snap.pieces}
            captured = self._prev_piece_ids - cur_ids
            if captured:
                self._sound_obs._play_sound("capture.wav")
            else:
                prev_snap = self._snapshot
                prev_airborne = {p.id for p in (prev_snap.pieces if prev_snap else [])
                                 if p.state == "airborne"}
                new_airborne = {p.id for p in snap.pieces if p.state == "airborne"}
                if new_airborne - prev_airborne:
                    self._sound_obs._play_sound("jump.wav")
                else:
                    self._sound_obs._play_sound("move.wav")
        self._prev_log_len   = new_log_len
        self._prev_piece_ids = {p.id for p in snap.pieces}

    # ------------------------------------------------------------------ network

    def _send(self, cmd: str) -> None:
        if self._ws and self._loop:
            asyncio.run_coroutine_threadsafe(self._ws.send(cmd), self._loop)

    async def _run_ws(self) -> None:
        self._loop = asyncio.get_event_loop()
        auth_msg = json.dumps(
            {"auth": self._username, "rejoin": self._game_id}
            if self._game_id is not None
            else {"auth": self._username}
        )
        try:
            async with websockets.connect(SERVER_URI) as ws:
                self._ws = ws
                await ws.send(auth_msg)
                async for raw in ws:
                    if self._user_closed:
                        break
                    data = json.loads(raw)
                    if "error" in data:
                        print(f"[client] Server error: {data['error']}")
                    elif "assigned" in data:
                        if data["assigned"] == "waiting":
                            print(f"[client] In matchmaking queue... (ELO: {data.get('elo', '?')})")
                        else:
                            self._color   = data["assigned"]
                            self._game_id = data.get("game_id")
                            if data.get("reconnected"):
                                print(f"[client] Reconnected as {self._color}")
                            else:
                                print(f"[client] Matched! You are {self._color}"
                                      f"  vs {data.get('opponent', '?')}"
                                      f" (ELO {data.get('opponent_elo', '?')})")
                            self._matched.set()
                    elif "matchmaking_timeout" in data:
                        print("[client] Matchmaking timed out. No opponent found.")
                        self._timed_out = True
                        self._matched.set()
                        break
                    elif "pieces" in data:
                        self._snapshot = parse_snapshot(data)
                    elif "elo_update" in data:
                        new_elo = data["elo_update"].get(self._username)
                        if new_elo is not None:
                            print(f"[client] Your new ELO: {new_elo}")
                    elif "opponent_disconnected" in data:
                        print("[client] Opponent disconnected — waiting for reconnect...")
                    elif "opponent_forfeited" in data:
                        print("[client] Opponent forfeited. You win!")
        except Exception:
            pass

    def _start_ws_thread(self) -> None:
        threading.Thread(target=lambda: asyncio.run(self._run_ws()), daemon=True).start()

    # ------------------------------------------------------------------ input

    def _piece_at(self, row: int, col: int) -> PieceSnapshot | None:
        if self._snapshot is None:
            return None
        return next((p for p in self._snapshot.pieces
                     if p.row == row and p.col == col and p.state != "captured"), None)

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        board_x = x - PANEL_W
        if board_x < 0 or self._snapshot is None or self._color is None:
            return
        try:
            pos = pixel_to_position(board_x, y, self._cell_size)
        except (ValueError, ZeroDivisionError):
            return
        if not (0 <= pos.row < self._snapshot.rows and 0 <= pos.col < self._snapshot.cols):
            return

        if event == cv2.EVENT_RBUTTONDOWN:
            piece = self._piece_at(pos.row, pos.col)
            if piece and piece.color == self._color[0]:
                self._send(encode_jump(piece.color, piece.kind, pos.row, pos.col))
            self._selected = None

        elif event == cv2.EVENT_LBUTTONDOWN:
            if self._selected is None:
                piece = self._piece_at(pos.row, pos.col)
                if piece and piece.color == self._color[0]:
                    self._selected = (pos.row, pos.col)
            else:
                sr, sc = self._selected
                piece = self._piece_at(sr, sc)
                if piece:
                    self._send(encode_move(piece.color, piece.kind, sr, sc, pos.row, pos.col))
                self._selected = None

    # ------------------------------------------------------------------ run

    def run(self) -> None:
        self._start_ws_thread()
        self._matched.wait(timeout=70)
        if self._timed_out or self._color is None:
            return
        self._run_loop()
