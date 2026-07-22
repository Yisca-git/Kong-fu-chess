"""CLI command implementations — all server calls go through WebSocket."""
from __future__ import annotations
import asyncio
import getpass
import json

import websockets

from client.config import SERVER_URI, REQUEST_TIMEOUT, MSG_LEADERBOARD


async def _ws_request(payload: dict) -> dict:
    """Sends a one-shot request to the server and returns the response."""
    async with websockets.connect(SERVER_URI) as ws:
        await ws.send(json.dumps(payload))
        raw = await asyncio.wait_for(ws.recv(), timeout=REQUEST_TIMEOUT)
        return json.loads(raw)


def _prompt_credentials() -> tuple[str, str]:
    username = input("  Username: ").strip()
    password = getpass.getpass("  Password: ")
    return username, password


def cmd_register() -> None:
    username, password = _prompt_credentials()
    try:
        result = asyncio.run(_ws_request({"register": True, "username": username, "password": password}))
        print(f"  {result.get('msg', 'Unknown response.')}")
    except Exception as e:
        print(f"  [error] Could not reach server: {e}")


def cmd_login() -> str | None:
    username, password = _prompt_credentials()
    try:
        result = asyncio.run(_ws_request({"login": True, "username": username, "password": password}))
        print(f"  {result.get('msg', 'Unknown response.')}")
        return username if result.get("ok") else None
    except Exception as e:
        print(f"  [error] Could not reach server: {e}")
        return None


def cmd_play(username: str) -> None:
    from client.ui.player_session import PlayerSession
    print(f"  Connecting to server as {username}...")
    PlayerSession(username=username).run()


def cmd_watch(username: str) -> None:
    try:
        result = asyncio.run(_ws_request({"auth": username, "list_games": True}))
    except Exception as e:
        print(f"  [error] Could not reach server: {e}")
        return
    games = result.get("games", [])
    if not games:
        print("  No active games.")
        return
    print("  Active games:")
    for g in games:
        print(f"    [{g['game_id']}] {g['white']} vs {g['black']}")
    try:
        game_id = int(input("  Enter game ID to watch: ").strip())
    except ValueError:
        print("  Invalid ID.")
        return
    from client.ui.spectator_session import SpectatorSession
    SpectatorSession(username=username, game_id=game_id).run()


def cmd_leaderboard() -> None:
    try:
        result = asyncio.run(_ws_request({"leaderboard": True}))
    except Exception as e:
        print(f"  [error] Could not reach server: {e}")
        return
    rows = result.get(MSG_LEADERBOARD, [])
    if not rows:
        print("  No players yet.")
        return
    print("  Rank  Player          ELO")
    for i, r in enumerate(rows, 1):
        print(f"  {i:<5} {r['username']:<15} {r['elo']}")
