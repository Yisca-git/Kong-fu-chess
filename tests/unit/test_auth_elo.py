"""Tests for server/services/elo.py and server/services/auth.py."""
import pytest
from server.services.elo import expected, updated_ratings


# ── ELO ──────────────────────────────────────────────────────────────────────

def test_expected_equal_ratings():
    assert abs(expected(1200, 1200) - 0.5) < 1e-9


def test_expected_higher_rating_wins_more():
    assert expected(1400, 1200) > 0.5


def test_expected_lower_rating_wins_less():
    assert expected(1000, 1200) < 0.5


def test_updated_ratings_winner_gains():
    new_w, new_l = updated_ratings(1200, 1200)
    assert new_w > 1200


def test_updated_ratings_loser_loses():
    new_w, new_l = updated_ratings(1200, 1200)
    assert new_l < 1200


def test_updated_ratings_sum_preserved():
    new_w, new_l = updated_ratings(1200, 1200)
    assert new_w + new_l == 2400


def test_updated_ratings_upset_bigger_gain():
    """Underdog winning should gain more than favourite winning."""
    new_w_upset, _ = updated_ratings(1000, 1400)   # underdog wins
    new_w_fav,   _ = updated_ratings(1400, 1000)   # favourite wins
    assert new_w_upset - 1000 > new_w_fav - 1400


# ── Auth ──────────────────────────────────────────────────────────────────────

def test_register_new_user(tmp_path, monkeypatch):
    import server.db.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    from server.services.auth import register
    ok, msg = register("alice", "secret")
    assert ok
    assert "success" in msg.lower()


def test_register_duplicate_fails(tmp_path, monkeypatch):
    import server.db.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    from server.services.auth import register
    register("alice", "secret")
    ok, msg = register("alice", "other")
    assert not ok


def test_login_correct_password(tmp_path, monkeypatch):
    import server.db.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    from server.services.auth import register, login
    register("bob", "pass123")
    ok, msg = login("bob", "pass123")
    assert ok


def test_login_wrong_password(tmp_path, monkeypatch):
    import server.db.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    from server.services.auth import register, login
    register("bob", "pass123")
    ok, _ = login("bob", "wrong")
    assert not ok


def test_login_unknown_user(tmp_path, monkeypatch):
    import server.db.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")
    db_module.init_db()
    from server.services.auth import login
    ok, _ = login("nobody", "x")
    assert not ok
