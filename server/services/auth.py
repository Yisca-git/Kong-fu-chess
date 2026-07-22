"""Authentication helpers: register, login, password hashing."""
from __future__ import annotations
import bcrypt
from server.db.db import get_user, create_user

# --- config ---
MSG_USERNAME_EXISTS = "Username already exists."
MSG_REGISTERED      = "Registered successfully."
MSG_USER_NOT_FOUND  = "User not found."
MSG_WRONG_PASSWORD  = "Wrong password."
MSG_WELCOME         = "Welcome, {username}! ELO: {elo}"


# --- private helpers ---
def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


# --- public API ---
def register(username: str, password: str) -> tuple[bool, str]:
    if get_user(username):
        return False, MSG_USERNAME_EXISTS
    create_user(username, _hash_password(password))
    return True, MSG_REGISTERED


def login(username: str, password: str) -> tuple[bool, str]:
    user = get_user(username)
    if not user:
        return False, MSG_USER_NOT_FOUND
    if not _verify_password(password, user["password_hash"]):
        return False, MSG_WRONG_PASSWORD
    return True, MSG_WELCOME.format(username=username, elo=user["elo"])
