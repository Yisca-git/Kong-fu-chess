"""SpectatorClient: read-only viewer for a live game."""
from __future__ import annotations
import asyncio
import json
import threading

import websockets

from client.protocol.codec import parse_snapshot
from client.ui.render_loop import RenderLoop
from client.config import SERVER_URI


class SpectatorClient(RenderLoop):
    """Renders a live game without sending any commands."""

    def __init__(self, username: str, game_id: int) -> None:
        super().__init__()
        self._username = username
        self._game_id  = game_id
        self._ready    = threading.Event()

    def _ready_event(self) -> threading.Event:
        return self._ready

    def _start_ws_thread(self) -> None:
        threading.Thread(target=lambda: asyncio.run(self._run_ws()), daemon=True).start()

    async def _run_ws(self) -> None:
        auth_msg = json.dumps({"auth": self._username, "watch": self._game_id})
        try:
            async with websockets.connect(SERVER_URI) as ws:
                await ws.send(auth_msg)
                async for raw in ws:
                    if self._user_closed:
                        break
                    data = json.loads(raw)
                    if "error" in data:
                        print(f"[spectator] {data['error']}")
                        break
                    elif "pieces" in data:
                        self._snapshot = parse_snapshot(data)
                        self._ready.set()
        except Exception:
            pass

    def run(self) -> None:
        self._start_ws_thread()
        if not self._ready.wait(timeout=10):
            print("[spectator] Could not connect to game.")
            return
        self._run_loop()
