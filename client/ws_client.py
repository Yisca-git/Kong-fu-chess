"""WebSocket client for KungFu Chess (Phase A+B).

Runs the OpenCV game window while communicating with ws_server over WebSocket.
The server owns the game state; the client only renders and sends commands.

Usage (direct):
    py -m client.ws_client
Usage (via CLI):
    py -m cli.shell
"""
from __future__ import annotations
import asyncio
import json
import sys
import os
import threading
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import cv2
import websockets

from engine.game_snapshot import GameSnapshot, PieceSnapshot
from engine.move_log import MoveEntry
from view.sprites.sprite_library import SpriteLibrary
from view.renderer import Renderer
from view.config import PANEL_W, TICK_MS, WINDOW_NAME

SERVER_URI = "ws://localhost:8765"


def _parse_snapshot(data: dict) -> GameSnapshot:
    pieces = tuple(
        PieceSnapshot(
            id=p["id"], color=p["color"], kind=p["kind"],
            row=p["row"], col=p["col"], state=p["state"],
            motion_progress=p["mp"],
            dest_row=p["dr"], dest_col=p["dc"],
            cooldown_progress=p["cp"],
        )
        for p in data["pieces"]
    )
    move_log = tuple(
        MoveEntry(e["color"], e["notation"], e["time_ms"])
        for e in data.get("move_log", [])
    )
    return GameSnapshot(
        pieces=pieces,
        game_over=data["game_over"],
        rows=data["rows"],
        cols=data["cols"],
        white_score=data["white_score"],
        black_score=data["black_score"],
        winner=data.get("winner"),
        white_name=data.get("white_name", "White"),
        black_name=data.get("black_name", "Black"),
        move_log=move_log,
        rejection_reason=data.get("rejection_reason"),
    )


_COL_LETTERS = "abcdefgh"


def _encode_move(color: str, kind: str, src_row: int, src_col: int,
                 dst_row: int, dst_col: int) -> str:
    c = "W" if color == "w" else "B"
    sc = _COL_LETTERS[src_col]; sr = 8 - src_row
    dc = _COL_LETTERS[dst_col]; dr = 8 - dst_row
    return f"{c}{kind}{sc}{sr}{dc}{dr}"


def _encode_jump(color: str, kind: str, row: int, col: int) -> str:
    c = "W" if color == "w" else "B"
    return f"{c}{kind}{_COL_LETTERS[col]}{8 - row}"


class NetworkClient:
    """Bridges the OpenCV window with the WebSocket server."""

    def __init__(self, username: str = "guest") -> None:
        self._username   = username
        self._renderer   = Renderer(SpriteLibrary())
        self._snapshot:  GameSnapshot | None = None
        self._color:     str | None = None
        self._selected:  tuple[int, int] | None = None
        self._ws         = None
        self._loop:      asyncio.AbstractEventLoop | None = None
        self._matched    = threading.Event()   # set when assigned white/black
        self._timed_out  = False

    # ------------------------------------------------------------------ network

    def _send(self, cmd: str) -> None:
        if self._ws and self._loop:
            asyncio.run_coroutine_threadsafe(self._ws.send(cmd), self._loop)

    async def _run_ws(self) -> None:
        self._loop = asyncio.get_event_loop()
        async with websockets.connect(SERVER_URI) as ws:
            self._ws = ws
            await ws.send(json.dumps({"auth": self._username}))
            async for raw in ws:
                data = json.loads(raw)
                if "error" in data:
                    print(f"[client] Server error: {data['error']}")
                elif "assigned" in data:
                    if data["assigned"] == "waiting":
                        print(f"[client] In matchmaking queue... (ELO: {data.get('elo', '?')})")
                    else:
                        self._color = data["assigned"]
                        opp = data.get('opponent', '?')
                        opp_elo = data.get('opponent_elo', '?')
                        print(f"[client] Matched! You are {self._color}  vs {opp} (ELO {opp_elo})")
                        self._matched.set()
                elif "matchmaking_timeout" in data:
                    print("[client] Matchmaking timed out. No opponent found.")
                    self._timed_out = True
                    self._matched.set()  # unblock run()
                    break
                elif "pieces" in data:
                    self._snapshot = _parse_snapshot(data)
                elif "elo_update" in data:
                    new_elo = data["elo_update"].get(self._username)
                    if new_elo is not None:
                        print(f"[client] Your new ELO: {new_elo}")

    def _start_ws_thread(self) -> None:
        def _thread():
            asyncio.run(self._run_ws())
        threading.Thread(target=_thread, daemon=True).start()

    # ------------------------------------------------------------------ input

    def _piece_at(self, row: int, col: int) -> PieceSnapshot | None:
        if self._snapshot is None:
            return None
        for p in self._snapshot.pieces:
            if p.row == row and p.col == col and p.state != "captured":
                return p
        return None

    def _on_mouse(self, event: int, x: int, y: int, flags: int, param) -> None:
        from input.board_mapper import pixel_to_position
        board_x = x - PANEL_W
        if board_x < 0 or self._snapshot is None or self._color is None:
            return
        try:
            pos = pixel_to_position(board_x, y)
        except ValueError:
            return
        if not (0 <= pos.row < self._snapshot.rows and 0 <= pos.col < self._snapshot.cols):
            return

        if event == cv2.EVENT_RBUTTONDOWN:
            piece = self._piece_at(pos.row, pos.col)
            if piece and piece.color == self._color[0]:
                self._send(_encode_jump(piece.color, piece.kind, pos.row, pos.col))
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
                    self._send(_encode_move(piece.color, piece.kind, sr, sc, pos.row, pos.col))
                self._selected = None

    # ------------------------------------------------------------------ render loop

    def run(self) -> None:
        self._start_ws_thread()

        # wait for match before opening window
        self._matched.wait(timeout=70)
        if self._timed_out or self._color is None:
            return

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(WINDOW_NAME, self._on_mouse)

        start_ms = time.monotonic() * 1000
        while True:
            now_ms = int(time.monotonic() * 1000 - start_ms)
            snap   = self._snapshot
            if snap is not None:
                canvas = self._renderer.render(snap, now_ms)
                cv2.imshow(WINDOW_NAME, canvas.raw())
                if snap.game_over:
                    cv2.waitKey(2000)  # 2 שניות להציג מסך סיום
                    break

            key = cv2.waitKey(TICK_MS) & 0xFF
            if key in (27, ord('q')):
                break
            if cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":
    NetworkClient().run()
