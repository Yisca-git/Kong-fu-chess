"""Tests for server/network/protocol.py and client/protocol/codec.py."""
import json
import pytest
from engine.game_snapshot import GameSnapshot, PieceSnapshot
from engine.move_log import MoveEntry
from server.network.protocol import encode_snapshot, decode_command
from client.protocol.codec import parse_snapshot, encode_move, encode_jump


def _minimal_snapshot(**kwargs) -> GameSnapshot:
    defaults = dict(
        pieces=(), game_over=False, rows=8, cols=8,
        white_score=0, black_score=0, move_log=(),
        winner=None, white_name="White", black_name="Black",
    )
    return GameSnapshot(**{**defaults, **kwargs})


# ── encode_snapshot ───────────────────────────────────────────────────────────

def test_encode_snapshot_is_valid_json():
    snap = _minimal_snapshot()
    assert json.loads(encode_snapshot(snap))


def test_encode_snapshot_game_over_false():
    snap = _minimal_snapshot(game_over=False)
    assert json.loads(encode_snapshot(snap))["game_over"] is False


def test_encode_snapshot_force_game_over():
    snap = _minimal_snapshot(game_over=False)
    assert json.loads(encode_snapshot(snap, force_game_over=True))["game_over"] is True


def test_encode_snapshot_winner_override():
    snap = _minimal_snapshot(winner=None)
    assert json.loads(encode_snapshot(snap, winner="w"))["winner"] == "w"


def test_encode_snapshot_includes_piece_fields():
    piece = PieceSnapshot(id="wR00", color="w", kind="R", row=0, col=0,
                          state="idle", motion_progress=1.0,
                          dest_row=None, dest_col=None, cooldown_progress=0.0)
    snap = _minimal_snapshot(pieces=(piece,))
    data = json.loads(encode_snapshot(snap))
    p = data["pieces"][0]
    assert p["id"] == "wR00"
    assert p["color"] == "w"
    assert p["state"] == "idle"


def test_encode_snapshot_includes_move_log():
    entry = MoveEntry("w", "Re2e4", 1000)
    snap  = _minimal_snapshot(move_log=(entry,))
    data  = json.loads(encode_snapshot(snap))
    assert data["move_log"][0]["notation"] == "Re2e4"


# ── decode_command ────────────────────────────────────────────────────────────

def test_decode_move_command():
    color, src, dst = decode_command("WRe2e4")
    assert color == "w"
    assert src == (6, 4)   # e2 → row=8-2=6, col=4
    assert dst == (4, 4)   # e4 → row=8-4=4, col=4


def test_decode_jump_command():
    color, src, dst = decode_command("WKe1")
    assert color == "w"
    assert src == (7, 4)   # e1 → row=8-1=7, col=4
    assert dst is None


def test_decode_black_command():
    color, src, dst = decode_command("BRa8a1")
    assert color == "b"
    assert src == (0, 0)
    assert dst == (7, 0)


# ── encode_move / encode_jump (client codec) ──────────────────────────────────

def test_encode_move_white():
    assert encode_move("w", "R", 6, 4, 4, 4) == "WRe2e4"


def test_encode_move_black():
    assert encode_move("b", "R", 0, 0, 7, 0) == "BRa8a1"


def test_encode_jump_white():
    assert encode_jump("w", "K", 7, 4) == "WKe1"


def test_encode_jump_black():
    assert encode_jump("b", "K", 0, 4) == "BKe8"


def test_encode_decode_roundtrip_move():
    cmd = encode_move("w", "Q", 7, 3, 4, 3)
    color, src, dst = decode_command(cmd)
    assert color == "w"
    assert src == (7, 3)
    assert dst == (4, 3)


def test_encode_decode_roundtrip_jump():
    cmd = encode_jump("b", "N", 0, 1)
    color, src, dst = decode_command(cmd)
    assert color == "b"
    assert src == (0, 1)
    assert dst is None


# ── parse_snapshot (client codec) ────────────────────────────────────────────

def test_parse_snapshot_basic():
    data = {
        "pieces": [], "game_over": False, "rows": 8, "cols": 8,
        "white_score": 0, "black_score": 0, "move_log": [],
        "winner": None, "white_name": "Alice", "black_name": "Bob",
        "rejection_reason": None,
    }
    snap = parse_snapshot(data)
    assert snap.white_name == "Alice"
    assert snap.rows == 8
    assert snap.game_over is False


def test_parse_snapshot_with_piece():
    data = {
        "pieces": [{"id": "wR00", "color": "w", "kind": "R",
                    "row": 0, "col": 0, "state": "idle",
                    "mp": 1.0, "dr": None, "dc": None, "cp": 0.0}],
        "game_over": False, "rows": 8, "cols": 8,
        "white_score": 3, "black_score": 0, "move_log": [],
        "winner": None, "white_name": "W", "black_name": "B",
        "rejection_reason": None,
    }
    snap = parse_snapshot(data)
    assert len(snap.pieces) == 1
    assert snap.pieces[0].id == "wR00"
    assert snap.white_score == 3


def test_parse_snapshot_with_move_log():
    data = {
        "pieces": [], "game_over": False, "rows": 8, "cols": 8,
        "white_score": 0, "black_score": 0,
        "move_log": [{"color": "w", "notation": "Re2e4", "time_ms": 1000}],
        "winner": None, "white_name": "W", "black_name": "B",
        "rejection_reason": None,
    }
    snap = parse_snapshot(data)
    assert len(snap.move_log) == 1
    assert snap.move_log[0].notation == "Re2e4"


def test_parse_encode_roundtrip():
    piece = PieceSnapshot(id="bN01", color="b", kind="N", row=0, col=1,
                          state="idle", motion_progress=1.0,
                          dest_row=None, dest_col=None, cooldown_progress=0.0)
    original = _minimal_snapshot(pieces=(piece,), white_name="X", black_name="Y")
    data = json.loads(encode_snapshot(original))
    restored = parse_snapshot(data)
    assert restored.white_name == "X"
    assert restored.pieces[0].id == "bN01"
