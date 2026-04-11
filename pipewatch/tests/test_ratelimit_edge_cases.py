"""Edge-case tests for pipewatch.ratelimit."""
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


def test_overwrite_limit_updates_quota(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 100.0)
    rl.set_limit("email", 2, 60)
    rl.set_limit("email", 10, 60)  # overwrite
    assert rl._limits["email"][0] == 10


def test_record_dispatch_without_set_limit_does_not_crash():
    # history created lazily
    rl.record_dispatch("orphan")
    assert "orphan" in rl._history


def test_window_boundary_exact(monkeypatch):
    """A timestamp exactly at window edge should be evicted."""
    tick = {"t": 1000.0}
    monkeypatch.setattr(rl, "_now", lambda: tick["t"])
    rl.set_limit("ch", 1, 60)
    rl.record_dispatch("ch")  # recorded at t=1000
    tick["t"] = 1060.0  # exactly 60 s later — outside window (> not >=)
    assert rl.is_rate_limited("ch") is False


def test_multiple_channels_independent(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 500.0)
    rl.set_limit("a", 1, 60)
    rl.set_limit("b", 5, 60)
    rl.record_dispatch("a")
    rl.record_dispatch("a")  # over limit for 'a'
    assert rl.is_rate_limited("a") is True
    assert rl.is_rate_limited("b") is False


def test_list_limits_empty_initially():
    assert rl.list_limits() == {}


def test_clear_then_re_register(monkeypatch):
    monkeypatch.setattr(rl, "_now", lambda: 300.0)
    rl.set_limit("email", 1, 30)
    rl.record_dispatch("email")
    assert rl.is_rate_limited("email") is True
    rl.clear_limit("email")
    rl.set_limit("email", 10, 30)
    # history cleared — should not be limited
    assert rl.is_rate_limited("email") is False
