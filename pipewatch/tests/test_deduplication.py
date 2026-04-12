"""Tests for pipewatch.deduplication."""

from __future__ import annotations

import time
import pytest

import pipewatch.deduplication as dedup


@pytest.fixture(autouse=True)
def reset_registry():
    dedup._registry.clear()
    dedup._windows.clear()
    yield
    dedup._registry.clear()
    dedup._windows.clear()


def test_is_duplicate_false_for_unknown_pipeline():
    assert dedup.is_duplicate("pipe_a", "warning") is False


def test_record_then_is_duplicate():
    dedup.record_alert("pipe_a", "warning")
    assert dedup.is_duplicate("pipe_a", "warning") is True


def test_different_level_not_duplicate():
    dedup.record_alert("pipe_a", "warning")
    assert dedup.is_duplicate("pipe_a", "critical") is False


def test_different_pipeline_not_duplicate():
    dedup.record_alert("pipe_a", "warning")
    assert dedup.is_duplicate("pipe_b", "warning") is False


def test_set_window_zero_always_duplicate(monkeypatch):
    """Window of 0 means any previously recorded alert is NOT within window."""
    dedup.set_window("pipe_a", "warning", 0)
    dedup.record_alert("pipe_a", "warning")
    # Advance time slightly
    original = dedup._now
    monkeypatch.setattr(dedup, "_now", lambda: original() + 0.001)
    assert dedup.is_duplicate("pipe_a", "warning") is False


def test_set_window_large_keeps_duplicate(monkeypatch):
    dedup.set_window("pipe_a", "warning", 9999)
    dedup.record_alert("pipe_a", "warning")
    assert dedup.is_duplicate("pipe_a", "warning") is True


def test_set_window_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        dedup.set_window("pipe_a", "warning", -1)


def test_clear_specific_level():
    dedup.record_alert("pipe_a", "warning")
    dedup.record_alert("pipe_a", "critical")
    dedup.clear("pipe_a", "warning")
    assert dedup.is_duplicate("pipe_a", "warning") is False
    assert dedup.is_duplicate("pipe_a", "critical") is True


def test_clear_all_levels_for_pipeline():
    dedup.record_alert("pipe_a", "warning")
    dedup.record_alert("pipe_a", "critical")
    dedup.clear("pipe_a")
    assert dedup.is_duplicate("pipe_a", "warning") is False
    assert dedup.is_duplicate("pipe_a", "critical") is False


def test_list_entries_empty():
    assert dedup.list_entries() == []


def test_list_entries_contains_recorded():
    dedup.record_alert("pipe_a", "warning")
    entries = dedup.list_entries()
    assert len(entries) == 1
    entry = entries[0]
    assert entry["pipeline"] == "pipe_a"
    assert entry["level"] == "warning"
    assert entry["last_alert_ago_seconds"] >= 0
    assert entry["window_seconds"] == dedup._DEFAULT_WINDOW_SECONDS


def test_list_entries_respects_custom_window():
    dedup.set_window("pipe_b", "critical", 60)
    dedup.record_alert("pipe_b", "critical")
    entries = dedup.list_entries()
    assert entries[0]["window_seconds"] == 60
