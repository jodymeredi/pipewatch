"""Tests for pipewatch/scheduling.py"""

from __future__ import annotations

import datetime
import pytest

import pipewatch.scheduling as sched


@pytest.fixture(autouse=True)
def reset_registry():
    sched._schedules.clear()
    yield
    sched._schedules.clear()


# ---------------------------------------------------------------------------
# set_schedule
# ---------------------------------------------------------------------------

def test_set_schedule_returns_dict():
    result = sched.set_schedule("etl_load", 3600)
    assert result == {"pipeline": "etl_load", "interval_seconds": 3600}


def test_set_schedule_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        sched.set_schedule("   ", 60)


def test_set_schedule_zero_interval_raises():
    with pytest.raises(ValueError, match="positive"):
        sched.set_schedule("etl_load", 0)


def test_set_schedule_negative_interval_raises():
    with pytest.raises(ValueError, match="positive"):
        sched.set_schedule("etl_load", -10)


def test_set_schedule_overwrites_previous():
    sched.set_schedule("etl_load", 3600)
    sched.set_schedule("etl_load", 600)
    assert sched.get_schedule("etl_load") == 600


# ---------------------------------------------------------------------------
# get_schedule / remove_schedule
# ---------------------------------------------------------------------------

def test_get_schedule_returns_none_when_missing():
    assert sched.get_schedule("unknown") is None


def test_remove_schedule_returns_true_when_present():
    sched.set_schedule("etl_load", 3600)
    assert sched.remove_schedule("etl_load") is True
    assert sched.get_schedule("etl_load") is None


def test_remove_schedule_returns_false_when_absent():
    assert sched.remove_schedule("ghost") is False


# ---------------------------------------------------------------------------
# list_schedules
# ---------------------------------------------------------------------------

def test_list_schedules_empty():
    assert sched.list_schedules() == []


def test_list_schedules_sorted():
    sched.set_schedule("z_pipe", 120)
    sched.set_schedule("a_pipe", 60)
    names = [r["pipeline"] for r in sched.list_schedules()]
    assert names == ["a_pipe", "z_pipe"]


# ---------------------------------------------------------------------------
# is_overdue
# ---------------------------------------------------------------------------

def test_is_overdue_false_when_no_schedule():
    last = datetime.datetime.utcnow() - datetime.timedelta(hours=24)
    assert sched.is_overdue("unregistered", last) is False


def test_is_overdue_true_when_no_last_run():
    sched.set_schedule("etl_load", 3600)
    assert sched.is_overdue("etl_load", None) is True


def test_is_overdue_false_within_interval():
    sched.set_schedule("etl_load", 3600)
    last = datetime.datetime.utcnow() - datetime.timedelta(seconds=100)
    assert sched.is_overdue("etl_load", last) is False


def test_is_overdue_true_past_interval():
    sched.set_schedule("etl_load", 3600)
    last = datetime.datetime.utcnow() - datetime.timedelta(seconds=7200)
    assert sched.is_overdue("etl_load", last) is True


# ---------------------------------------------------------------------------
# overdue_pipelines
# ---------------------------------------------------------------------------

def test_overdue_pipelines_returns_overdue_only():
    sched.set_schedule("slow", 60)
    sched.set_schedule("fast", 3600)
    last_runs = {
        "slow": datetime.datetime.utcnow() - datetime.timedelta(seconds=200),
        "fast": datetime.datetime.utcnow() - datetime.timedelta(seconds=10),
    }
    result = sched.overdue_pipelines(last_runs)
    assert "slow" in result
    assert "fast" not in result


def test_overdue_pipelines_missing_key_treated_as_none():
    sched.set_schedule("etl_load", 3600)
    result = sched.overdue_pipelines({})
    assert "etl_load" in result
