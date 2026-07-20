"""CLI entry point for KungFu Chess."""
from __future__ import annotations
import asyncio
import json
import sys
import os
import getpass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import websockets

from server.db import init_db, get_all_users
from server.auth import register, login

SERVER_URI = "ws://localhost:8765"


def _prompt_credentials() -> tuple[str, str]:
    username = input("  Username: ").strip()
    password = getpass.getpass("  Password: ")
    return username, password


async def _fetch_games(username: str) -> list[dict]:
    try:
        async with websockets.connect(SERVER_URI) as ws:
            await ws.send(json.dumps({"auth": username, "list_games": True}))
            raw = await asyncio.wait_for(ws.recv(), timeout=5)
            return json.loads(raw).get("games", [])
    except Exception:
        return []


def main() -> None:
    init_db()
    print("=== KungFu Chess ===")

    logged_in_user: str | None = None

    while True:
        if logged_in_user:
            cmd = input(f"\n[{logged_in_user}] > play / watch / leaderboard / logout / quit: ").strip().lower()
        else:
            cmd = input("\n> register / login / quit: ").strip().lower()

        if cmd == "quit":
            break

        elif cmd == "register":
            username, password = _prompt_credentials()
            ok, msg = register(username, password)
            print(f"  {msg}")

        elif cmd == "login":
            username, password = _prompt_credentials()
            ok, msg = login(username, password)
            print(f"  {msg}")
            if ok:
                logged_in_user = username

        elif cmd == "play" and logged_in_user:
            print(f"  Connecting to server as {logged_in_user}...")
            from client.ws_client import NetworkClient
            NetworkClient(username=logged_in_user).run()

        elif cmd == "watch" and logged_in_user:
            games = asyncio.run(_fetch_games(logged_in_user))
            if not games:
                print("  No active games.")
                continue
            print("  Active games:")
            for g in games:
                print(f"    [{g['game_id']}] {g['white']} vs {g['black']}")
            try:
                game_id = int(input("  Enter game ID to watch: ").strip())
            except ValueError:
                print("  Invalid ID.")
                continue
            from client.ws_client import SpectatorClient
            SpectatorClient(username=logged_in_user, game_id=game_id).run()

        elif cmd == "leaderboard":
            rows = get_all_users()
            if not rows:
                print("  No players yet.")
            else:
                print("  Rank  Player          ELO")
                for i, r in enumerate(rows, 1):
                    print(f"  {i:<5} {r['username']:<15} {r['elo']}")

        elif cmd == "logout" and logged_in_user:
            logged_in_user = None

        else:
            print("  Unknown command.")


if __name__ == "__main__":
    main()
