"""SpectatorClient: pure WebSocket spectator — no UI dependencies."""
from __future__ import annotations
import asyncio
import json
import threading
from typing import Callable

import websockets

from engine.game_snapshot import GameSnapshot
from client.protocol.codec import parse_snapshot
from client.config import SERVER_URI

OnSnapshot = Callable[[GameSnapshot], None]


class SpectatorClient:
    """Pure WebSocket spectator. Owns no UI — caller injects on_snapshot."""

    def __init__(self, username: str, game_id: int,
                 on_snapshot: OnSnapshot) -> None:
        self._username    = username
        self._game_id     = game_id
        self._on_snapshot = on_snapshot
        self.ready        = threading.Event()
        self.user_closed  = False

    def start(self) -> None:
        threading.Thread(target=lambda: asyncio.run(self._run_ws()), daemon=True).start()

    async def _run_ws(self) -> None:
        auth_msg = json.dumps({"auth": self._username, "watch": self._game_id})
        try:
            async with websockets.connect(SERVER_URI) as ws:
                await ws.send(auth_msg)
                async for raw in ws:
                    if self.user_closed:
                        break
                    data = json.loads(raw)
                    if "error" in data:
                        print(f"[spectator] Server error: {data['error']}")
                        break
                    elif "pieces" in data:
                        self._on_snapshot(parse_snapshot(data))
                        self.ready.set()
        except OSError as e:
            print(f"[spectator] Connection error: {e}")
        except json.JSONDecodeError as e:
            print(f"[spectator] Invalid message from server: {e}")
