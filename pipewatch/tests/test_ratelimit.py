"""Tests for pipewatch.ratelimit."""
from __future__ import annotations

import pytest

import pipewatch.ratelimit as rl


@pytest.fixture(autouse=True)
def reset_registry():
    rl._limits.clear()
    rl._history.clear()
    yield
    rl._limits.clear()
    rl._history.clear()


# ── set_limit ────────────────────────────────────────────────────────────────

def test_set_limit_registers_channel():
    rl.set_limit("email", 5, 60)
    assert "email" in rl._limits
    assert rl._limits["email"] == (5, 60)


def test_set_limit_zero_max_calls_raises():
    with pytest.raises(ValueError, match="max_calls"):
        rl.set_limit("email", 0, 60)


def test_set_limit_negative_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        rl.set_limit("email", 3, -1)


# ── is_rate_limited ──────────────────────────────────────────────────────────

def test_is_rate_limited_false_for_unknown_channel():
    assert rl.is_rate_limited("webhook") is False


def test_is_rate_limited_false_when_under_quota(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 1000.0)
    rl.set_limit("email", 3, 60)
    rl.record_dispatch("email")
    rl.record_dispatch("email")
    assert rl.is_rate_limited("email") is False


def test_is_rate_limited_true_when_quota_exhausted(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 1000.0)
    rl.set_limit("email", 2, 60)
    rl.record_dispatch("email")
    rl.record_dispatch("email")
    assert rl.is_rate_limited("email") is True


def test_is_rate_limited_resets_after_window(monkeypatch):
    tick = {"t": 1000.0}
    monkeypatch.setattr(rl, "_now", lambda: tick["t"])
    rl.set_limit("email", 2, 60)
    rl.record_dispatch("email")
    rl.record_dispatch("email")
    assert rl.is_rate_limited("email") is True
    tick["t"] = 1065.0  # past the 60 s window
    assert rl.is_rate_limited("email") is False


# ── remaining ────────────────────────────────────────────────────────────────

def test_remaining_unlimited_for_unknown_channel():
    assert rl.remaining("slack") == -1


def test_remaining_decrements_with_dispatches(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 500.0)
    rl.set_limit("slack", 5, 30)
    assert rl.remaining("slack") == 5
    rl.record_dispatch("slack")
    assert rl.remaining("slack") == 4


def test_remaining_never_below_zero(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 500.0)
    rl.set_limit("slack", 1, 30)
    rl.record_dispatch("slack")
    rl.record_dispatch("slack")  # over limit
    assert rl.remaining("slack") == 0


# ── clear_limit ──────────────────────────────────────────────────────────────

def test_clear_limit_removes_channel():
    rl.set_limit("email", 3, 60)
    assert rl.clear_limit("email") is True
    assert "email" not in rl._limits


def test_clear_limit_returns_false_for_unknown():
    assert rl.clear_limit("nonexistent") is False


# ── list_limits ──────────────────────────────────────────────────────────────

def test_list_limits_returns_all_channels():
    rl.set_limit("email", 5, 60)
    rl.set_limit("webhook", 10, 30)
    result = rl.list_limits()
    assert set(result.keys()) == {"email", "webhook"}
    assert result["email"] == {"max_calls": 5, "window_seconds": 60}
