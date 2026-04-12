"""Tests for pipewatch.priority."""

import pytest

from pipewatch import priority as _mod
from pipewatch.priority import (
    clear_priorities,
    get_priority,
    list_priorities,
    remove_priority,
    set_priority,
    sort_by_priority,
    _DEFAULT_PRIORITY,
)


@pytest.fixture(autouse=True)
def reset_registry():
    clear_priorities()
    yield
    clear_priorities()


# ---------------------------------------------------------------------------
# set_priority
# ---------------------------------------------------------------------------

def test_set_priority_returns_dict():
    result = set_priority("ingest", 10)
    assert result == {"pipeline": "ingest", "priority": 10}


def test_set_priority_blank_pipeline_raises():
    with pytest.raises(ValueError, match="non-blank"):
        set_priority("  ", 5)


def test_set_priority_level_zero_raises():
    with pytest.raises(ValueError, match="between 1 and 100"):
        set_priority("ingest", 0)


def test_set_priority_level_101_raises():
    with pytest.raises(ValueError, match="between 1 and 100"):
        set_priority("ingest", 101)


def test_set_priority_boundary_values_accepted():
    set_priority("a", 1)
    set_priority("b", 100)
    assert get_priority("a") == 1
    assert get_priority("b") == 100


def test_set_priority_overwrites_previous():
    set_priority("ingest", 20)
    set_priority("ingest", 5)
    assert get_priority("ingest") == 5


# ---------------------------------------------------------------------------
# get_priority
# ---------------------------------------------------------------------------

def test_get_priority_returns_default_when_unset():
    assert get_priority("unknown-pipeline") == _DEFAULT_PRIORITY


def test_get_priority_strips_whitespace():
    set_priority("ingest", 15)
    assert get_priority("  ingest  ") == 15


# ---------------------------------------------------------------------------
# remove_priority
# ---------------------------------------------------------------------------

def test_remove_priority_returns_true_when_present():
    set_priority("ingest", 10)
    assert remove_priority("ingest") is True


def test_remove_priority_returns_false_when_absent():
    assert remove_priority("ghost") is False


def test_remove_priority_falls_back_to_default_afterwards():
    set_priority("ingest", 3)
    remove_priority("ingest")
    assert get_priority("ingest") == _DEFAULT_PRIORITY


# ---------------------------------------------------------------------------
# list_priorities
# ---------------------------------------------------------------------------

def test_list_priorities_empty_when_none_set():
    assert list_priorities() == []


def test_list_priorities_sorted_by_level():
    set_priority("c", 30)
    set_priority("a", 10)
    set_priority("b", 20)
    names = [e["pipeline"] for e in list_priorities()]
    assert names == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# sort_by_priority
# ---------------------------------------------------------------------------

def test_sort_by_priority_orders_correctly():
    set_priority("low", 80)
    set_priority("high", 5)
    result = sort_by_priority(["low", "high", "medium"])
    assert result[0] == "high"
    assert result[-1] == "low"


def test_sort_by_priority_uses_default_for_unregistered():
    set_priority("critical", 1)
    result = sort_by_priority(["normal", "critical"])
    assert result[0] == "critical"
