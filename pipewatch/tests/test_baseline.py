"""Tests for pipewatch.baseline."""

import json
import os
import pytest

import pipewatch.baseline as bl


@pytest.fixture(autouse=True)
def reset_registry():
    bl.clear_baselines()
    yield
    bl.clear_baselines()


def test_set_baseline_returns_dict():
    result = bl.set_baseline("etl_daily", "row_count", 1000.0)
    assert result == {"pipeline": "etl_daily", "metric": "row_count", "baseline": 1000.0}


def test_get_baseline_returns_value():
    bl.set_baseline("etl_daily", "row_count", 500.0)
    assert bl.get_baseline("etl_daily", "row_count") == 500.0


def test_get_baseline_returns_none_when_missing():
    assert bl.get_baseline("nonexistent", "row_count") is None


def test_remove_baseline_returns_true_when_present():
    bl.set_baseline("p1", "latency", 2.0)
    assert bl.remove_baseline("p1", "latency") is True
    assert bl.get_baseline("p1", "latency") is None


def test_remove_baseline_returns_false_when_absent():
    assert bl.remove_baseline("ghost", "latency") is False


def test_remove_baseline_cleans_empty_pipeline():
    bl.set_baseline("p1", "m", 1.0)
    bl.remove_baseline("p1", "m")
    assert "p1" not in bl.list_baselines()


def test_compare_no_breach_within_tolerance():
    bl.set_baseline("pipe", "rows", 1000.0)
    result = bl.compare_to_baseline("pipe", "rows", 1050.0, tolerance=0.1)
    assert result is not None
    assert result["breached"] is False
    assert abs(result["deviation"] - 0.05) < 1e-6


def test_compare_breach_outside_tolerance():
    bl.set_baseline("pipe", "rows", 1000.0)
    result = bl.compare_to_baseline("pipe", "rows", 1200.0, tolerance=0.1)
    assert result["breached"] is True


def test_compare_returns_none_when_no_baseline():
    result = bl.compare_to_baseline("pipe", "unknown_metric", 42.0)
    assert result is None


def test_compare_zero_baseline_nonzero_current():
    bl.set_baseline("pipe", "errors", 0.0)
    result = bl.compare_to_baseline("pipe", "errors", 5.0)
    assert result["deviation"] == float("inf")
    assert result["breached"] is True


def test_compare_zero_baseline_zero_current():
    bl.set_baseline("pipe", "errors", 0.0)
    result = bl.compare_to_baseline("pipe", "errors", 0.0)
    assert result["deviation"] == 0.0
    assert result["breached"] is False


def test_list_baselines_returns_all():
    bl.set_baseline("a", "m1", 1.0)
    bl.set_baseline("b", "m2", 2.0)
    listing = bl.list_baselines()
    assert listing == {"a": {"m1": 1.0}, "b": {"m2": 2.0}}


def test_save_and_load_baselines(tmp_path):
    bl.set_baseline("pipe", "rows", 999.0)
    bl.save_baselines(str(tmp_path))
    bl.clear_baselines()
    assert bl.get_baseline("pipe", "rows") is None
    bl.load_baselines(str(tmp_path))
    assert bl.get_baseline("pipe", "rows") == 999.0


def test_load_baselines_missing_file_resets(tmp_path):
    bl.set_baseline("pipe", "rows", 1.0)
    bl.load_baselines(str(tmp_path))  # file doesn't exist
    assert bl.list_baselines() == {}
