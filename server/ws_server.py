"""WebSocket server for KungFu Chess (Phase A+B).

Run:
    py -m server.ws_server

Slots: first connection = White, second = Black.
First message from client must be: {"auth": "<username>"}
Command format: "WQe2e4" (move) or "WKe1" (jump).
"""
from __future__ import annotations
import asyncio
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets
from websockets.server import WebSocketServerProtocol

from model.position import Position
from server.game_session import GameSession
from server.protocol import decode_command, encode_snapshot
from server.db import init_db, get_user, update_elo
from server.elo import updated_ratings

HOST = "localhost"
PORT = 8765

_slots:     dict[int, WebSocketServerProtocol] = {}
_usernames: dict[int, str] = {}   # slot → username
_session:   GameSession | None = None


async def _broadcast(payload: str) -> None:
    for ws in list(_slots.values()):
        try:
            await ws.send(payload)
        except Exception:
            pass


def _on_state(payload: str) -> None:
    asyncio.get_event_loop().create_task(_broadcast(payload))


def _on_game_over(winner: str) -> None:
    asyncio.get_event_loop().create_task(_settle_elo(winner))


async def _settle_elo(winner: str) -> None:
    """Compute and persist updated ELO for both players after game ends."""
    if len(_usernames) < 2:
        return
    white_name = _usernames.get(0)
    black_name = _usernames.get(1)
    if not white_name or not black_name:
        return
    white_user = get_user(white_name)
    black_user = get_user(black_name)
    if not white_user or not black_user:
        return

    if winner == "w":
        new_w, new_b = updated_ratings(white_user["elo"], black_user["elo"])
    else:
        new_b, new_w = updated_ratings(black_user["elo"], white_user["elo"])

    update_elo(white_name, new_w)
    update_elo(black_name, new_b)
    print(f"[server] ELO updated — {white_name}: {white_user['elo']}→{new_w}  "
          f"{black_name}: {black_user['elo']}→{new_b}")
    await _broadcast(json.dumps({
        "elo_update": {
            white_name: new_w,
            black_name: new_b,
        }
    }))


async def _handle(ws: WebSocketServerProtocol) -> None:
    global _session

    # assign slot
    slot = 0 if 0 not in _slots else (1 if 1 not in _slots else None)
    if slot is None:
        await ws.close(1008, "Game is full")
        return

    # first message must be auth
    try:
        raw      = await asyncio.wait_for(ws.recv(), timeout=10)
        auth     = json.loads(raw)
        username = auth.get("auth", "")
        user     = get_user(username)
        if not user:
            await ws.send(json.dumps({"error": "Unknown user. Please register first."}))
            await ws.close()
            return
    except Exception:
        await ws.close(1008, "Auth timeout or invalid message")
        return

    _slots[slot]     = ws
    _usernames[slot] = username
    color = "white" if slot == 0 else "black"
    print(f"[server] {username} (ELO {user['elo']}) connected as {color}")
    await ws.send(json.dumps({"assigned": color, "elo": user["elo"]}))

    # start game when both players are connected
    if len(_slots) == 2 and _session is None:
        w = _usernames.get(0, "White")
        b = _usernames.get(1, "Black")
        _session = GameSession(on_state=_on_state, on_game_over=_on_game_over,
                                  white_name=w, black_name=b)
        _session.start()
        print(f"[server] Game started: {w} vs {b}")
    elif _session is not None:
        # send immediate snapshot to late-joining slot
        await ws.send(encode_snapshot(_session.engine.snapshot()))

    try:
        async for message in ws:
            if _session is None:
                continue
            try:
                _color, src, dst = decode_command(message)
                engine  = _session.engine
                src_pos = Position(*src)
                if dst is None:
                    result = engine.request_jump(src_pos)
                else:
                    result = engine.request_move(src_pos, Position(*dst))
                if not result.is_accepted:
                    await ws.send(json.dumps({"rejection": result.reason}))
            except Exception as e:
                await ws.send(json.dumps({"error": str(e)}))
    finally:
        _slots.pop(slot, None)
        _usernames.pop(slot, None)
        print(f"[server] slot {slot} disconnected")
        if not _slots:
            if _session:
                _session.stop()
            _session = None


async def main() -> None:
    init_db()
    print(f"[server] Listening on ws://{HOST}:{PORT}")
    async with websockets.serve(_handle, HOST, PORT):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
