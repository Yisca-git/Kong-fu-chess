"""CLI entry point for KungFu Chess."""
from __future__ import annotations
from server.db.db import init_db
from cli.commands import cmd_register, cmd_login, cmd_play, cmd_watch, cmd_leaderboard


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
            cmd_register()
        elif cmd == "login":
            logged_in_user = cmd_login()
        elif cmd == "play" and logged_in_user:
            cmd_play(logged_in_user)
        elif cmd == "watch" and logged_in_user:
            cmd_watch(logged_in_user)
        elif cmd == "leaderboard":
            cmd_leaderboard()
        elif cmd == "logout" and logged_in_user:
            logged_in_user = None
        else:
            print("  Unknown command.")


if __name__ == "__main__":
    main()
