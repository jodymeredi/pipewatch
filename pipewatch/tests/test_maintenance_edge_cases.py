"""Edge-case tests for pipewatch.maintenance."""

from datetime import datetime, timedelta, timezone

import pytest

import pipewatch.maintenance as maint


@pytest.fixture(autouse=True)
def reset_registry():
    maint._registry.clear()
    yield
    maint._registry.clear()


def _future(m: int = 30) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=m)


def _past(m: int = 30) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=m)


def test_pipeline_name_stripped():
    w = maint.add_window("  pipe_a  ", _future(5), _future(30))
    assert w["pipeline"] == "pipe_a"


def test_reason_stripped():
    w = maint.add_window("pipe_a", _future(5), _future(30), reason="  deploy  ")
    assert w["reason"] == "deploy"


def test_blank_created_by_defaults_to_system():
    w = maint.add_window("pipe_a", _future(5), _future(30), created_by="  ")
    assert w["created_by"] == "system"


def test_two_windows_same_pipeline_both_active():
    maint.add_window("pipe_a", _past(5), _future(10))
    maint.add_window("pipe_a", _past(2), _future(20))
    assert maint.is_in_maintenance("pipe_a") is True
    assert len(maint.list_windows(pipeline="pipe_a")) == 2


def test_list_windows_returns_copies():
    maint.add_window("pipe_a", _future(5), _future(30))
    result = maint.list_windows()
    result[0]["pipeline"] = "tampered"
    assert maint.list_windows()[0]["pipeline"] == "pipe_a"


def test_purge_expired_with_empty_registry_returns_zero():
    assert maint.purge_expired() == 0


def test_is_in_maintenance_at_exact_start_boundary():
    now = datetime.now(timezone.utc)
    maint.add_window("pipe_a", now, _future(30))
    assert maint.is_in_maintenance("pipe_a", at=now) is True


def test_is_in_maintenance_at_exact_end_boundary():
    end = _future(30)
    maint.add_window("pipe_a", _future(5), end)
    assert maint.is_in_maintenance("pipe_a", at=end) is True
