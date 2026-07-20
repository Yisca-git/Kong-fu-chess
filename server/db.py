"""SQLite persistence layer.

Schema:
  users(id, username, password_hash, elo)
  game_log(id, game_id, event, detail, ts)
"""
from __future__ import annotations
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "kungfu_chess.db"


def _connect() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _connect() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                elo           INTEGER NOT NULL DEFAULT 1200
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS game_log (
                id      INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id INTEGER NOT NULL,
                event   TEXT    NOT NULL,
                detail  TEXT    NOT NULL DEFAULT '',
                ts      DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


def get_user(username: str) -> sqlite3.Row | None:
    with _connect() as con:
        return con.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()


def create_user(username: str, password_hash: str) -> None:
    with _connect() as con:
        con.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )


def update_elo(username: str, new_elo: int) -> None:
    with _connect() as con:
        con.execute(
            "UPDATE users SET elo = ? WHERE username = ?", (new_elo, username)
        )


def log_event(game_id: int, event: str, detail: str = "") -> None:
    with _connect() as con:
        con.execute(
            "INSERT INTO game_log (game_id, event, detail) VALUES (?, ?, ?)",
            (game_id, event, detail),
        )


def get_all_users() -> list[sqlite3.Row]:
    with _connect() as con:
        return con.execute(
            "SELECT username, elo FROM users ORDER BY elo DESC"
        ).fetchall()
