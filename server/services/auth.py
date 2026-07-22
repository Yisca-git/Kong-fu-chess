"""Authentication helpers: register, login, password hashing."""
from __future__ import annotations
import bcrypt
from server.db.db import get_user, create_user


def register(username: str, password: str) -> tuple[bool, str]:
    if get_user(username):
        return False, "Username already exists."
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    create_user(username, hashed)
    return True, "Registered successfully."


def login(username: str, password: str) -> tuple[bool, str]:
    user = get_user(username)
    if not user:
        return False, "User not found."
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        return False, "Wrong password."
    return True, f"Welcome, {username}! ELO: {user['elo']}"
