"""Tests for pipewatch.throttle."""

from __future__ import annotations

import pytest
import pipewatch.throttle as throttle


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure a clean throttle registry for every test."""
    throttle.reset_all()
    yield
    throttle.reset_all()


def test_is_throttled_returns_false_for_unknown_pipeline():
    assert throttle.is_throttled("unknown_pipe") is False


def test_set_cooldown_registers_pipeline():
    throttle.set_cooldown("pipe_a", cooldown_seconds=60)
    entries = throttle.list_throttles()
    assert "pipe_a" in entries
    assert entries["pipe_a"]["cooldown_seconds"] == 60


def test_set_cooldown_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        throttle.set_cooldown("pipe_x", cooldown_seconds=-1)


def test_record_alert_then_is_throttled(monkeypatch):
    monkeypatch.setattr(throttle, "_now", lambda: 1_000.0)
    throttle.record_alert("pipe_b", cooldown_seconds=120)
    # Still within cooldown window
    assert throttle.is_throttled("pipe_b") is True


def test_record_alert_not_throttled_after_cooldown(monkeypatch):
    monkeypatch.setattr(throttle, "_now", lambda: 1_000.0)
    throttle.record_alert("pipe_c", cooldown_seconds=60)

    # Advance time beyond cooldown
    monkeypatch.setattr(throttle, "_now", lambda: 1_061.0)
    assert throttle.is_throttled("pipe_c") is False


def test_record_alert_preserves_existing_cooldown(monkeypatch):
    monkeypatch.setattr(throttle, "_now", lambda: 500.0)
    throttle.set_cooldown("pipe_d", cooldown_seconds=90)
    throttle.record_alert("pipe_d")  # no explicit cooldown
    entries = throttle.list_throttles()
    assert entries["pipe_d"]["cooldown_seconds"] == 90


def test_clear_throttle_removes_entry():
    throttle.set_cooldown("pipe_e", cooldown_seconds=30)
    removed = throttle.clear_throttle("pipe_e")
    assert removed is True
    assert "pipe_e" not in throttle.list_throttles()


def test_clear_throttle_returns_false_for_missing():
    assert throttle.clear_throttle("nonexistent") is False


def test_list_throttles_remaining_seconds(monkeypatch):
    monkeypatch.setattr(throttle, "_now", lambda: 2_000.0)
    throttle.record_alert("pipe_f", cooldown_seconds=100)

    monkeypatch.setattr(throttle, "_now", lambda: 2_040.0)
    entries = throttle.list_throttles()
    assert abs(entries["pipe_f"]["remaining_seconds"] - 60.0) < 0.01
    assert entries["pipe_f"]["throttled"] is True


def test_reset_all_clears_everything():
    throttle.set_cooldown("pipe_g")
    throttle.set_cooldown("pipe_h")
    throttle.reset_all()
    assert throttle.list_throttles() == {}
