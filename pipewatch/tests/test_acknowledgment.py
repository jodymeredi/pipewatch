"""Tests for pipewatch.acknowledgment."""

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
def reset_registry():
    ack_mod._registry.clear()
    yield
    ack_mod._registry.clear()


def _future(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def _past(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


def test_acknowledge_returns_dict():
    result = acknowledge("pipe_a", "critical", "alice")
    assert result["pipeline"] == "pipe_a"
    assert result["level"] == "critical"
    assert result["acknowledged_by"] == "alice"
    assert "id" in result
    assert "acknowledged_at" in result


def test_acknowledge_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline"):
        acknowledge("  ", "warning", "alice")


def test_acknowledge_blank_user_raises():
    with pytest.raises(ValueError, match="acknowledged_by"):
        acknowledge("pipe_a", "warning", "  ")


def test_acknowledge_invalid_level_raises():
    with pytest.raises(ValueError, match="level"):
        acknowledge("pipe_a", "unknown", "alice")


def test_is_acknowledged_true_when_active():
    acknowledge("pipe_a", "warning", "bob")
    assert is_acknowledged("pipe_a", "warning") is True


def test_is_acknowledged_false_for_unknown():
    assert is_acknowledged("pipe_x", "critical") is False


def test_is_acknowledged_false_for_different_level():
    acknowledge("pipe_a", "warning", "bob")
    assert is_acknowledged("pipe_a", "critical") is False


def test_is_acknowledged_false_after_expiry():
    acknowledge("pipe_a", "critical", "carol", expires_at=_past())
    assert is_acknowledged("pipe_a", "critical") is False


def test_is_acknowledged_true_before_expiry():
    acknowledge("pipe_a", "critical", "carol", expires_at=_future())
    assert is_acknowledged("pipe_a", "critical") is True


def test_clear_acknowledgment_returns_true():
    acknowledge("pipe_a", "warning", "dave")
    assert clear_acknowledgment("pipe_a") is True
    assert is_acknowledged("pipe_a", "warning") is False


def test_clear_acknowledgment_returns_false_when_missing():
    assert clear_acknowledgment("no_such_pipe") is False


def test_get_acknowledgment_returns_copy():
    acknowledge("pipe_a", "ok", "eve", note="all good")
    result = get_acknowledgment("pipe_a")
    assert result is not None
    assert result["note"] == "all good"


def test_get_acknowledgment_returns_none_for_missing():
    assert get_acknowledgment("ghost") is None


def test_list_acknowledgments_reflects_entries():
    acknowledge("pipe_a", "warning", "frank")
    acknowledge("pipe_b", "critical", "grace")
    names = {e["pipeline"] for e in list_acknowledgments()}
    assert names == {"pipe_a", "pipe_b"}


def test_acknowledge_overwrites_previous():
    acknowledge("pipe_a", "warning", "h1")
    acknowledge("pipe_a", "critical", "h2")
    entry = get_acknowledgment("pipe_a")
    assert entry["level"] == "critical"
    assert entry["acknowledged_by"] == "h2"
