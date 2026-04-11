"""Tests for pipewatch.silencer."""

from datetime import datetime, timedelta, timezone

import pytest

from pipewatch import silencer
from pipewatch.silencer import (
    add_silence,
    clear_all_silences,
    is_silenced,
    list_silences,
    remove_expired_silences,
)


@pytest.fixture(autouse=True)
def reset_registry():
    """Ensure each test starts with an empty silence registry."""
    clear_all_silences()
    yield
    clear_all_silences()


def _future(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def _past(seconds: int = 3600) -> datetime:
    return datetime.now(timezone.utc) - timedelta(seconds=seconds)


# ---------------------------------------------------------------------------
# add_silence / list_silences
# ---------------------------------------------------------------------------

def test_add_silence_returns_rule_dict():
    rule = add_silence("etl_*", reason="maintenance")
    assert rule["pipeline_pattern"] == "etl_*"
    assert rule["reason"] == "maintenance"
    assert rule["expires_at"] is None
    assert rule["statuses"] is None


def test_list_silences_reflects_added_rules():
    add_silence("pipe_a", reason="test")
    add_silence("pipe_b", reason="test2")
    rules = list_silences()
    assert len(rules) == 2


def test_list_silences_returns_copy():
    add_silence("pipe_a", reason="test")
    rules = list_silences()
    rules.clear()
    assert len(list_silences()) == 1


# ---------------------------------------------------------------------------
# is_silenced
# ---------------------------------------------------------------------------

def test_is_silenced_matches_exact_name():
    add_silence("my_pipeline", reason="test", expires_at=_future())
    assert is_silenced("my_pipeline", "critical") is True


def test_is_silenced_uses_glob_pattern():
    add_silence("etl_*", reason="test", expires_at=_future())
    assert is_silenced("etl_sales", "warning") is True
    assert is_silenced("reporting_sales", "warning") is False


def test_is_silenced_respects_status_filter():
    add_silence("pipe", reason="test", expires_at=_future(), statuses=["warning"])
    assert is_silenced("pipe", "warning") is True
    assert is_silenced("pipe", "critical") is False


def test_is_silenced_status_case_insensitive():
    add_silence("pipe", reason="test", expires_at=_future(), statuses=["WARNING"])
    assert is_silenced("pipe", "warning") is True


def test_is_silenced_expired_rule_returns_false():
    add_silence("pipe", reason="test", expires_at=_past())
    assert is_silenced("pipe", "critical") is False


def test_is_silenced_no_rules_returns_false():
    assert is_silenced("any_pipeline", "critical") is False


# ---------------------------------------------------------------------------
# remove_expired_silences
# ---------------------------------------------------------------------------

def test_remove_expired_silences_removes_past_rules():
    add_silence("pipe_a", reason="old", expires_at=_past())
    add_silence("pipe_b", reason="current", expires_at=_future())
    removed = remove_expired_silences()
    assert removed == 1
    assert len(list_silences()) == 1


def test_remove_expired_silences_keeps_no_expiry_rules():
    add_silence("pipe_a", reason="permanent")
    removed = remove_expired_silences()
    assert removed == 0
    assert len(list_silences()) == 1
