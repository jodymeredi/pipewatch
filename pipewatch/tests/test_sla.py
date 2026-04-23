"""Tests for pipewatch.sla."""

from __future__ import annotations

import datetime
import pytest

import pipewatch.sla as sla_mod
from pipewatch.sla import (
    set_sla,
    get_sla,
    remove_sla,
    list_slas,
    check_sla,
)


@pytest.fixture(autouse=True)
def reset_registry():
    sla_mod._registry.clear()
    yield
    sla_mod._registry.clear()


# --- set_sla ---

def test_set_sla_returns_dict():
    result = set_sla("etl.daily", "06:00")
    assert result["pipeline"] == "etl.daily"
    assert result["deadline_utc"] == "06:00"
    assert result["window_minutes"] == 60


def test_set_sla_custom_window():
    result = set_sla("etl.daily", "08:30", window_minutes=15)
    assert result["window_minutes"] == 15


def test_set_sla_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        set_sla("  ", "06:00")


def test_set_sla_invalid_deadline_raises():
    with pytest.raises(ValueError, match="HH:MM"):
        set_sla("pipe", "6am")


def test_set_sla_out_of_range_hour_raises():
    with pytest.raises(ValueError, match="out of range"):
        set_sla("pipe", "25:00")


def test_set_sla_negative_window_raises():
    with pytest.raises(ValueError, match="window_minutes"):
        set_sla("pipe", "06:00", window_minutes=-1)


def test_set_sla_overwrites_existing():
    set_sla("pipe", "06:00", window_minutes=30)
    set_sla("pipe", "08:00", window_minutes=10)
    assert get_sla("pipe")["deadline_utc"] == "08:00"


# --- get_sla / remove_sla / list_slas ---

def test_get_sla_returns_none_when_missing():
    assert get_sla("nonexistent") is None


def test_remove_sla_returns_true_when_present():
    set_sla("pipe", "06:00")
    assert remove_sla("pipe") is True


def test_remove_sla_returns_false_when_absent():
    assert remove_sla("ghost") is False


def test_list_slas_reflects_registered():
    set_sla("a", "01:00")
    set_sla("b", "02:00")
    names = {r["pipeline"] for r in list_slas()}
    assert names == {"a", "b"}


# --- check_sla ---

def test_check_sla_unknown_when_no_rule():
    result = check_sla("missing")
    assert result["status"] == "unknown"


def test_check_sla_ok_when_deadline_not_reached(monkeypatch):
    # Set deadline far in the future (23:59)
    set_sla("pipe", "23:59", window_minutes=0)
    future = datetime.datetime(2024, 1, 1, 0, 0, 0)
    monkeypatch.setattr(sla_mod, "_utcnow", lambda: future)
    result = check_sla("pipe")
    assert result["status"] == "ok"


def test_check_sla_ok_when_completed_before_deadline(monkeypatch):
    set_sla("pipe", "06:00", window_minutes=30)
    now = datetime.datetime(2024, 1, 1, 7, 0, 0)
    last_run = datetime.datetime(2024, 1, 1, 5, 50, 0)
    monkeypatch.setattr(sla_mod, "_utcnow", lambda: now)
    result = check_sla("pipe", last_run_utc=last_run)
    assert result["status"] == "ok"


def test_check_sla_breached_when_past_cutoff(monkeypatch):
    set_sla("pipe", "06:00", window_minutes=30)
    now = datetime.datetime(2024, 1, 1, 7, 0, 0)  # 1 hour past deadline
    monkeypatch.setattr(sla_mod, "_utcnow", lambda: now)
    result = check_sla("pipe", last_run_utc=None)
    assert result["status"] == "breached"
    assert "06:00" in result["message"]


def test_check_sla_breached_within_grace_window(monkeypatch):
    set_sla("pipe", "06:00", window_minutes=60)
    now = datetime.datetime(2024, 1, 1, 6, 30, 0)  # within grace window
    monkeypatch.setattr(sla_mod, "_utcnow", lambda: now)
    result = check_sla("pipe", last_run_utc=None)
    assert result["status"] == "breached"
    assert "grace" in result["message"]
