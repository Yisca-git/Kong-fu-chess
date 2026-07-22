"""WebSocket server entry point for KungFu Chess."""
from __future__ import annotations
import asyncio
import websockets

from server.db.db import init_db
from server.services.matchmaking import MatchmakingQueue
from server.core.server_state import ServerState
from server.network.handlers import handle

HOST = "localhost"
PORT = 8765


async def main() -> None:
    init_db()
    state = ServerState()
    state.queue = MatchmakingQueue(on_match=state.create_game)
    state.queue.start()
    print(f"[server] Listening on ws://{HOST}:{PORT}")
    async with websockets.serve(lambda ws: handle(ws, state), HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
