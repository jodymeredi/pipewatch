"""Integration tests: baseline interacting with metrics evaluation."""

import pytest

import pipewatch.baseline as bl
from pipewatch.metrics import collect_metric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    bl.clear_baselines()
    yield
    bl.clear_baselines()


def _make_metric(pipeline, value, warn=None, crit=None):
    thresholds = {}
    if warn is not None:
        thresholds["warning"] = warn
    if crit is not None:
        thresholds["critical"] = crit
    return collect_metric(pipeline, "row_count", value, thresholds=thresholds)


def test_baseline_breach_detected_alongside_ok_threshold():
    """Metric within threshold but deviates heavily from baseline."""
    bl.set_baseline("etl", "row_count", 1000.0)
    metric = _make_metric("etl", 1500.0, warn=2000.0, crit=3000.0)
    breaches = evaluate_thresholds([metric])
    # No threshold breach
    assert all(b["pipeline"] != "etl" for b in breaches)
    # But baseline deviation is significant
    result = bl.compare_to_baseline("etl", "row_count", metric.value)
    assert result["breached"] is True
    assert result["deviation"] == pytest.approx(0.5)


def test_baseline_ok_when_within_tolerance():
    bl.set_baseline("etl", "row_count", 1000.0)
    result = bl.compare_to_baseline("etl", "row_count", 980.0, tolerance=0.05)
    assert result["breached"] is False


def test_multiple_pipelines_independent_baselines():
    bl.set_baseline("pipe_a", "row_count", 500.0)
    bl.set_baseline("pipe_b", "row_count", 200.0)
    r_a = bl.compare_to_baseline("pipe_a", "row_count", 550.0)
    r_b = bl.compare_to_baseline("pipe_b", "row_count", 100.0)
    assert r_a["breached"] is False  # 10% deviation, tolerance default 10%
    assert r_b["breached"] is True   # 50% deviation


def test_save_reload_preserves_comparison(tmp_path):
    bl.set_baseline("pipe", "row_count", 300.0)
    bl.save_baselines(str(tmp_path))
    bl.clear_baselines()
    bl.load_baselines(str(tmp_path))
    result = bl.compare_to_baseline("pipe", "row_count", 360.0, tolerance=0.1)
    assert result["breached"] is True
