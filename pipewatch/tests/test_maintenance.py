"""Unit tests for pipewatch.maintenance."""

from datetime import datetime, timedelta, timezone

import pytest

import pipewatch.maintenance as maint


@pytest.fixture(autouse=True)
def reset_registry():
    maint._registry.clear()
    yield
    maint._registry.clear()


def _future(offset_minutes: int = 30) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)


def _past(offset_minutes: int = 30) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=offset_minutes)


def test_add_window_returns_dict():
    w = maint.add_window("pipe_a", _future(5), _future(60), reason="deploy")
    assert w["pipeline"] == "pipe_a"
    assert w["reason"] == "deploy"
    assert "id" in w


def test_add_window_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        maint.add_window("  ", _future(5), _future(60))


def test_add_window_ends_before_starts_raises():
    with pytest.raises(ValueError, match="ends_at"):
        maint.add_window("pipe_a", _future(60), _future(5))


def test_add_window_equal_times_raises():
    t = _future(10)
    with pytest.raises(ValueError):
        maint.add_window("pipe_a", t, t)


def test_is_in_maintenance_true_during_window():
    maint.add_window("pipe_a", _past(10), _future(10))
    assert maint.is_in_maintenance("pipe_a") is True


def test_is_in_maintenance_false_before_window():
    maint.add_window("pipe_a", _future(10), _future(60))
    assert maint.is_in_maintenance("pipe_a") is False


def test_is_in_maintenance_false_after_window():
    maint.add_window("pipe_a", _past(60), _past(10))
    assert maint.is_in_maintenance("pipe_a") is False


def test_is_in_maintenance_false_for_unregistered_pipeline():
    assert maint.is_in_maintenance("unknown") is False


def test_remove_window_returns_true():
    w = maint.add_window("pipe_a", _future(5), _future(30))
    assert maint.remove_window(w["id"]) is True


def test_remove_window_returns_false_for_missing_id():
    assert maint.remove_window("nonexistent-id") is False


def test_remove_window_stops_maintenance():
    w = maint.add_window("pipe_a", _past(10), _future(10))
    maint.remove_window(w["id"])
    assert maint.is_in_maintenance("pipe_a") is False


def test_list_windows_returns_all():
    maint.add_window("pipe_a", _future(5), _future(30))
    maint.add_window("pipe_b", _future(5), _future(30))
    assert len(maint.list_windows()) == 2


def test_list_windows_filtered_by_pipeline():
    maint.add_window("pipe_a", _future(5), _future(30))
    maint.add_window("pipe_b", _future(5), _future(30))
    result = maint.list_windows(pipeline="pipe_a")
    assert len(result) == 1
    assert result[0]["pipeline"] == "pipe_a"


def test_purge_expired_removes_old_windows():
    maint.add_window("pipe_a", _past(60), _past(10))
    maint.add_window("pipe_b", _future(5), _future(30))
    removed = maint.purge_expired()
    assert removed == 1
    assert len(maint.list_windows()) == 1


def test_purge_expired_returns_zero_when_none_expired():
    maint.add_window("pipe_a", _future(5), _future(30))
    assert maint.purge_expired() == 0
