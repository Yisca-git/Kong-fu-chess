"""CLI command implementations."""
from __future__ import annotations
import asyncio
import json
import getpass

import websockets

from server.db.db import get_all_users
from server.services.auth import register, login
from client.config import SERVER_URI


def prompt_credentials() -> tuple[str, str]:
    username = input("  Username: ").strip()
    password = getpass.getpass("  Password: ")
    return username, password


def cmd_register() -> None:
    username, password = prompt_credentials()
    _, msg = register(username, password)
    print(f"  {msg}")


def cmd_login() -> str | None:
    username, password = prompt_credentials()
    ok, msg = login(username, password)
    print(f"  {msg}")
    return username if ok else None


def cmd_play(username: str) -> None:
    from client.network.network_client import NetworkClient
    print(f"  Connecting to server as {username}...")
    NetworkClient(username=username).run()


def cmd_watch(username: str) -> None:
    games = asyncio.run(_fetch_games(username))
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
    from client.network.spectator_client import SpectatorClient
    SpectatorClient(username=username, game_id=game_id).run()


def cmd_leaderboard() -> None:
    rows = get_all_users()
    if not rows:
        print("  No players yet.")
        return
    print("  Rank  Player          ELO")
    for i, r in enumerate(rows, 1):
        print(f"  {i:<5} {r['username']:<15} {r['elo']}")


async def _fetch_games(username: str) -> list[dict]:
    try:
        async with websockets.connect(SERVER_URI) as ws:
            await ws.send(json.dumps({"auth": username, "list_games": True}))
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            return json.loads(raw).get("games", [])
    except Exception:
        return []
