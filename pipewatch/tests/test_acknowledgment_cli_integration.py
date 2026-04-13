"""CLI-style integration tests for acknowledgment (function-level simulation)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import pipewatch.acknowledgment as ack_mod
from pipewatch.acknowledgment import (
    acknowledge,
    clear_acknowledgment,
    get_acknowledgment,
    is_acknowledged,
    list_acknowledgments,
)


@pytest.fixture(autouse=True)
def reset():
    ack_mod._registry.clear()
    yield
    ack_mod._registry.clear()


def _simulate_ack(pipeline: str, level: str, user: str, note: str = "") -> dict:
    return acknowledge(pipeline, level, user, note=note)


def _simulate_status(pipeline: str, level: str) -> bool:
    return is_acknowledged(pipeline, level)


def _simulate_clear(pipeline: str) -> bool:
    return clear_acknowledgment(pipeline)


def _simulate_list() -> list:
    return list_acknowledgments()


def test_ack_returns_correct_dict():
    result = _simulate_ack("etl_daily", "critical", "ops")
    assert result["pipeline"] == "etl_daily"
    assert result["level"] == "critical"
    assert result["acknowledged_by"] == "ops"


def test_status_true_after_ack():
    _simulate_ack("etl_daily", "warning", "ops")
    assert _simulate_status("etl_daily", "warning") is True


def test_status_false_after_clear():
    _simulate_ack("etl_daily", "warning", "ops")
    _simulate_clear("etl_daily")
    assert _simulate_status("etl_daily", "warning") is False


def test_list_empty_initially():
    assert _simulate_list() == []


def test_list_shows_all_entries():
    _simulate_ack("pipe_a", "warning", "alice")
    _simulate_ack("pipe_b", "critical", "bob")
    names = {e["pipeline"] for e in _simulate_list()}
    assert names == {"pipe_a", "pipe_b"}


def test_get_acknowledgment_after_ack():
    _simulate_ack("pipe_a", "ok", "carol", note="routine check")
    entry = get_acknowledgment("pipe_a")
    assert entry is not None
    assert entry["note"] == "routine check"


def test_clear_nonexistent_returns_false():
    assert _simulate_clear("nonexistent") is False
