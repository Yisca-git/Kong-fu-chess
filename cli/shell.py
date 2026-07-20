"""CLI entry point for KungFu Chess.

Usage:
    py -m cli.shell

Commands:
    register  — create a new account
    login     — log in and launch the game client
    quit      — exit
"""
from __future__ import annotations
import sys
import os
import getpass
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.db import init_db
from server.auth import register, login


def _prompt_credentials() -> tuple[str, str]:
    username = input("  Username: ").strip()
    password = getpass.getpass("  Password: ")
    return username, password


def main() -> None:
    init_db()
    print("=== KungFu Chess ===")

    logged_in_user: str | None = None

    while True:
        if logged_in_user:
            cmd = input(f"\n[{logged_in_user}] > play / logout / quit: ").strip().lower()
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

        elif cmd == "logout" and logged_in_user:
            logged_in_user = None

        else:
            print("  Unknown command.")


if __name__ == "__main__":
    main()
