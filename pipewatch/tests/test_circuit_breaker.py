"""Tests for pipewatch.circuit_breaker."""

import pytest
import pipewatch.circuit_breaker as cb
from pipewatch.circuit_breaker import CLOSED, OPEN, HALF_OPEN


@pytest.fixture(autouse=True)
def reset_registry():
    cb._registry.clear()
    yield
    cb._registry.clear()


def test_register_breaker_returns_dict():
    result = cb.register_breaker("pipe_a")
    assert result["pipeline"] == "pipe_a"
    assert result["state"] == CLOSED
    assert result["failures"] == 0


def test_register_breaker_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        cb.register_breaker("   ")


def test_register_breaker_zero_threshold_raises():
    with pytest.raises(ValueError, match="threshold"):
        cb.register_breaker("pipe_a", threshold=0)


def test_register_breaker_negative_cooldown_raises():
    with pytest.raises(ValueError, match="cooldown"):
        cb.register_breaker("pipe_a", cooldown=-1.0)


def test_remove_breaker_returns_true_when_present():
    cb.register_breaker("pipe_a")
    assert cb.remove_breaker("pipe_a") is True


def test_remove_breaker_returns_false_when_absent():
    assert cb.remove_breaker("ghost") is False


def test_get_state_returns_none_for_unknown_pipeline():
    assert cb.get_state("unknown") is None


def test_get_state_closed_initially():
    cb.register_breaker("pipe_a")
    assert cb.get_state("pipe_a") == CLOSED


def test_record_failure_below_threshold_stays_closed():
    cb.register_breaker("pipe_a", threshold=3)
    cb.record_failure("pipe_a")
    cb.record_failure("pipe_a")
    assert cb.get_state("pipe_a") == CLOSED


def test_record_failure_at_threshold_opens_circuit():
    cb.register_breaker("pipe_a", threshold=3)
    for _ in range(3):
        cb.record_failure("pipe_a")
    assert cb.get_state("pipe_a") == OPEN


def test_record_failure_auto_registers_unknown_pipeline():
    state = cb.record_failure("new_pipe")
    assert state in (CLOSED, OPEN)
    assert "new_pipe" in cb._registry


def test_record_success_resets_failures():
    cb.register_breaker("pipe_a", threshold=2)
    cb.record_failure("pipe_a")
    cb.record_failure("pipe_a")
    assert cb.get_state("pipe_a") == OPEN
    cb.record_success("pipe_a")
    assert cb.get_state("pipe_a") == CLOSED
    assert cb._registry["pipe_a"]["failures"] == 0


def test_record_success_unknown_pipeline_returns_closed():
    result = cb.record_success("ghost")
    assert result == CLOSED


def test_half_open_after_cooldown(monkeypatch):
    cb.register_breaker("pipe_a", threshold=1, cooldown=30.0)
    cb.record_failure("pipe_a")
    assert cb.get_state("pipe_a") == OPEN
    # Simulate cooldown elapsed
    monkeypatch.setattr(cb, "_now", lambda: cb._registry["pipe_a"]["opened_at"] + 31.0)
    assert cb.get_state("pipe_a") == HALF_OPEN


def test_list_breakers_returns_all():
    cb.register_breaker("pipe_a")
    cb.register_breaker("pipe_b")
    names = [e["pipeline"] for e in cb.list_breakers()]
    assert "pipe_a" in names
    assert "pipe_b" in names


def test_list_breakers_returns_copies():
    cb.register_breaker("pipe_a")
    listing = cb.list_breakers()
    listing[0]["failures"] = 999
    assert cb._registry["pipe_a"]["failures"] == 0
