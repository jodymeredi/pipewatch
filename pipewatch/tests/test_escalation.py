"""Tests for pipewatch.escalation."""

from __future__ import annotations

import pytest

from pipewatch import escalation as esc


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure a clean breach registry before every test."""
    esc.reset_registry()
    yield
    esc.reset_registry()


# ---------------------------------------------------------------------------
# record_breach
# ---------------------------------------------------------------------------

def test_record_breach_stores_entry():
    esc.record_breach("pipe_a", "warning", _ts=1000.0)
    breaches = esc.list_breaches()
    assert "pipe_a" in breaches
    assert breaches["pipe_a"]["level"] == "warning"
    assert breaches["pipe_a"]["first_breach_at"] == 1000.0


def test_record_breach_same_level_preserves_timestamp():
    esc.record_breach("pipe_a", "critical", _ts=1000.0)
    esc.record_breach("pipe_a", "critical", _ts=2000.0)
    assert esc.list_breaches()["pipe_a"]["first_breach_at"] == 1000.0


def test_record_breach_level_change_resets_timestamp():
    esc.record_breach("pipe_a", "warning", _ts=1000.0)
    esc.record_breach("pipe_a", "critical", _ts=2000.0)
    entry = esc.list_breaches()["pipe_a"]
    assert entry["level"] == "critical"
    assert entry["first_breach_at"] == 2000.0


# ---------------------------------------------------------------------------
# clear_breach
# ---------------------------------------------------------------------------

def test_clear_breach_removes_entry():
    esc.record_breach("pipe_b", "warning", _ts=1000.0)
    esc.clear_breach("pipe_b")
    assert "pipe_b" not in esc.list_breaches()


def test_clear_breach_unknown_pipeline_is_noop():
    esc.clear_breach("nonexistent")  # should not raise


# ---------------------------------------------------------------------------
# should_escalate
# ---------------------------------------------------------------------------

def test_should_escalate_false_for_unknown_pipeline():
    assert esc.should_escalate("pipe_x") is False


def test_should_escalate_false_before_window():
    esc.record_breach("pipe_c", "warning", _ts=1000.0)
    # Only 100 s have passed; window is 300 s
    assert esc.should_escalate("pipe_c", window=300, _ts=1100.0) is False


def test_should_escalate_true_at_window_boundary():
    esc.record_breach("pipe_c", "warning", _ts=1000.0)
    assert esc.should_escalate("pipe_c", window=300, _ts=1300.0) is True


def test_should_escalate_true_after_window():
    esc.record_breach("pipe_c", "critical", _ts=0.0)
    assert esc.should_escalate("pipe_c", window=60, _ts=500.0) is True


def test_should_escalate_false_after_clear():
    esc.record_breach("pipe_d", "warning", _ts=0.0)
    esc.clear_breach("pipe_d")
    assert esc.should_escalate("pipe_d", window=0, _ts=999.0) is False


# ---------------------------------------------------------------------------
# list_breaches
# ---------------------------------------------------------------------------

def test_list_breaches_returns_copy():
    esc.record_breach("pipe_e", "warning", _ts=1.0)
    copy = esc.list_breaches()
    copy["pipe_e"]["level"] = "mutated"
    # Original registry should be unaffected
    assert esc.list_breaches()["pipe_e"]["level"] == "warning"
