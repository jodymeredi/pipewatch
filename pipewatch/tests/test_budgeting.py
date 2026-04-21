"""Tests for pipewatch.budgeting."""

from __future__ import annotations

import pytest

import pipewatch.budgeting as budgeting
from pipewatch.budgeting import (
    clear_budget,
    get_budget,
    is_over_budget,
    list_budgets,
    record_alert,
    remaining,
    remove_budget,
    reset_all,
    set_budget,
)

# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_registry():
    reset_all()
    yield
    reset_all()


# ---------------------------------------------------------------------------
# set_budget
# ---------------------------------------------------------------------------


def test_set_budget_returns_dict():
    result = set_budget("pipe_a", max_alerts=5, window_seconds=3600)
    assert result["pipeline"] == "pipe_a"
    assert result["max_alerts"] == 5
    assert result["window_seconds"] == 3600


def test_set_budget_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        set_budget("  ", max_alerts=3, window_seconds=60)


def test_set_budget_zero_max_alerts_raises():
    with pytest.raises(ValueError, match="max_alerts"):
        set_budget("pipe_a", max_alerts=0, window_seconds=60)


def test_set_budget_negative_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        set_budget("pipe_a", max_alerts=3, window_seconds=-1)


def test_set_budget_overwrites_existing():
    set_budget("pipe_a", max_alerts=5, window_seconds=3600)
    result = set_budget("pipe_a", max_alerts=10, window_seconds=7200)
    assert result["max_alerts"] == 10
    assert result["window_seconds"] == 7200


# ---------------------------------------------------------------------------
# get / remove / list
# ---------------------------------------------------------------------------


def test_get_budget_returns_none_for_unknown():
    assert get_budget("unknown") is None


def test_remove_budget_returns_true_when_present():
    set_budget("pipe_a", max_alerts=3, window_seconds=60)
    assert remove_budget("pipe_a") is True


def test_remove_budget_returns_false_when_absent():
    assert remove_budget("nonexistent") is False


def test_list_budgets_reflects_registered():
    set_budget("pipe_a", max_alerts=3, window_seconds=60)
    set_budget("pipe_b", max_alerts=1, window_seconds=30)
    names = {b["pipeline"] for b in list_budgets()}
    assert names == {"pipe_a", "pipe_b"}


# ---------------------------------------------------------------------------
# is_over_budget / record_alert / remaining
# ---------------------------------------------------------------------------


def test_is_over_budget_false_for_unknown():
    assert is_over_budget("unknown") is False


def test_remaining_none_for_unknown():
    assert remaining("unknown") is None


def test_remaining_equals_max_when_no_alerts_fired():
    set_budget("pipe_a", max_alerts=5, window_seconds=3600)
    assert remaining("pipe_a") == 5


def test_record_alert_decrements_remaining():
    set_budget("pipe_a", max_alerts=3, window_seconds=3600)
    record_alert("pipe_a")
    assert remaining("pipe_a") == 2


def test_is_over_budget_true_after_max_alerts():
    set_budget("pipe_a", max_alerts=2, window_seconds=3600)
    record_alert("pipe_a")
    record_alert("pipe_a")
    assert is_over_budget("pipe_a") is True


def test_remaining_floors_at_zero():
    set_budget("pipe_a", max_alerts=1, window_seconds=3600)
    record_alert("pipe_a")
    record_alert("pipe_a")  # extra — still 0, not negative
    assert remaining("pipe_a") == 0


def test_record_alert_unknown_pipeline_does_not_crash():
    record_alert("ghost")  # no budget registered — should be a no-op


def test_expired_firings_not_counted(monkeypatch):
    """Firings older than the window should be purged and not count."""
    set_budget("pipe_a", max_alerts=1, window_seconds=60)

    # Simulate a firing that happened 120 seconds ago
    entry = budgeting._registry["pipe_a"]
    import time
    entry["fired"].append(time.time() - 120)

    # Budget should be available again since the old firing expired
    assert is_over_budget("pipe_a") is False
    assert remaining("pipe_a") == 1
