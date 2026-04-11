"""Simulate CLI-level interactions with the rate-limit module."""
from __future__ import annotations

import pytest

import pipewatch.ratelimit as rl


@pytest.fixture(autouse=True)
def reset():
    rl._limits.clear()
    rl._history.clear()
    yield
    rl._limits.clear()
    rl._history.clear()


def _simulate_set(channel, max_calls, window):
    rl.set_limit(channel, max_calls, window)
    return rl.list_limits()[channel]


def _simulate_status(channel):
    return {
        "limited": rl.is_rate_limited(channel),
        "remaining": rl.remaining(channel),
    }


def _simulate_remove(channel):
    return rl.clear_limit(channel)


def test_set_returns_correct_dict():
    result = _simulate_set("webhook", 3, 120)
    assert result == {"max_calls": 3, "window_seconds": 120}


def test_status_shows_not_limited_initially(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 0.0)
    _simulate_set("webhook", 3, 120)
    status = _simulate_status("webhook")
    assert status["limited"] is False
    assert status["remaining"] == 3


def test_status_after_dispatches(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 0.0)
    _simulate_set("email", 2, 60)
    rl.record_dispatch("email")
    status = _simulate_status("email")
    assert status["limited"] is False
    assert status["remaining"] == 1
    rl.record_dispatch("email")
    status2 = _simulate_status("email")
    assert status2["limited"] is True
    assert status2["remaining"] == 0


def test_remove_clears_channel():
    _simulate_set("slack", 5, 30)
    ok = _simulate_remove("slack")
    assert ok is True
    assert "slack" not in rl.list_limits()


def test_remove_nonexistent_returns_false():
    assert _simulate_remove("ghost") is False


def test_list_shows_multiple_channels():
    _simulate_set("email", 5, 60)
    _simulate_set("webhook", 20, 10)
    _simulate_set("slack", 3, 300)
    limits = rl.list_limits()
    assert len(limits) == 3
    assert all(k in limits for k in ("email", "webhook", "slack"))
