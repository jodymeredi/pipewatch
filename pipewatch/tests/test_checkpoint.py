"""Tests for pipewatch.checkpoint."""

from __future__ import annotations

import time
import pytest

import pipewatch.checkpoint as cp


@pytest.fixture(autouse=True)
def reset_registry():
    cp._registry.clear()
    yield
    cp._registry.clear()


# ---------------------------------------------------------------------------
# record_checkpoint
# ---------------------------------------------------------------------------

def test_record_checkpoint_returns_dict():
    result = cp.record_checkpoint("etl", "extract")
    assert result["pipeline"] == "etl"
    assert result["stage"] == "extract"
    assert isinstance(result["recorded_at"], float)


def test_record_checkpoint_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline"):
        cp.record_checkpoint("  ", "extract")


def test_record_checkpoint_blank_stage_raises():
    with pytest.raises(ValueError, match="stage"):
        cp.record_checkpoint("etl", "")


def test_record_checkpoint_overwrites_previous():
    cp.record_checkpoint("etl", "extract")
    first = cp.get_checkpoint("etl", "extract")
    time.sleep(0.02)
    cp.record_checkpoint("etl", "extract")
    second = cp.get_checkpoint("etl", "extract")
    assert second > first


# ---------------------------------------------------------------------------
# get_checkpoint / list_checkpoints
# ---------------------------------------------------------------------------

def test_get_checkpoint_returns_none_when_missing():
    assert cp.get_checkpoint("etl", "load") is None


def test_list_checkpoints_returns_all_stages():
    cp.record_checkpoint("etl", "extract")
    cp.record_checkpoint("etl", "transform")
    cp.record_checkpoint("etl", "load")
    items = cp.list_checkpoints("etl")
    stages = [i["stage"] for i in items]
    assert set(stages) == {"extract", "transform", "load"}


def test_list_checkpoints_empty_for_unknown_pipeline():
    assert cp.list_checkpoints("ghost") == []


# ---------------------------------------------------------------------------
# remove_checkpoint
# ---------------------------------------------------------------------------

def test_remove_checkpoint_returns_true_when_present():
    cp.record_checkpoint("etl", "extract")
    assert cp.remove_checkpoint("etl", "extract") is True


def test_remove_checkpoint_returns_false_when_missing():
    assert cp.remove_checkpoint("etl", "nonexistent") is False


def test_remove_last_stage_cleans_up_pipeline_key():
    cp.record_checkpoint("etl", "extract")
    cp.remove_checkpoint("etl", "extract")
    assert "etl" not in cp._registry


# ---------------------------------------------------------------------------
# is_stale
# ---------------------------------------------------------------------------

def test_is_stale_false_for_recent_checkpoint():
    cp.record_checkpoint("etl", "extract")
    assert cp.is_stale("etl", "extract", max_age_seconds=3600) is False


def test_is_stale_false_for_missing_checkpoint():
    assert cp.is_stale("etl", "missing", max_age_seconds=1) is False


def test_is_stale_true_when_old(monkeypatch):
    cp.record_checkpoint("etl", "extract")
    monkeypatch.setattr(cp, "_now", lambda: time.time() + 7200)
    assert cp.is_stale("etl", "extract", max_age_seconds=3600) is True


def test_is_stale_zero_max_age_raises():
    with pytest.raises(ValueError):
        cp.is_stale("etl", "extract", max_age_seconds=0)


# ---------------------------------------------------------------------------
# clear_pipeline
# ---------------------------------------------------------------------------

def test_clear_pipeline_returns_count():
    cp.record_checkpoint("etl", "extract")
    cp.record_checkpoint("etl", "load")
    assert cp.clear_pipeline("etl") == 2


def test_clear_pipeline_unknown_returns_zero():
    assert cp.clear_pipeline("ghost") == 0
