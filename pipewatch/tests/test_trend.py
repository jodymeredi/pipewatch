"""Tests for pipewatch.trend module."""

import json
import os
import pytest

from pipewatch.trend import (
    analyze_trend,
    summarize_trends,
    TrendResult,
    _extract_series,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_snapshots(tmp_path, entries_per_snap):
    """Write one JSONL history file with one snapshot per list entry."""
    hist_dir = tmp_path / "history"
    hist_dir.mkdir()
    fpath = hist_dir / "pipeline_a.jsonl"
    with fpath.open("w") as fh:
        for metrics in entries_per_snap:
            snap = {"metrics": metrics}
            fh.write(json.dumps(snap) + "\n")
    return str(hist_dir)


def _metric_entry(pipeline, name, value):
    return {"pipeline": pipeline, "name": name, "value": value}


# ---------------------------------------------------------------------------
# _extract_series
# ---------------------------------------------------------------------------

def test_extract_series_returns_values(tmp_path):
    entries = [
        [_metric_entry("pipe_a", "row_count", 100)],
        [_metric_entry("pipe_a", "row_count", 110)],
        [_metric_entry("pipe_a", "row_count", 120)],
    ]
    hist_dir = _write_snapshots(tmp_path, entries)
    from pipewatch.history import load_snapshots
    snaps = load_snapshots(hist_dir)
    series = _extract_series(snaps, "pipe_a", "row_count")
    assert series == [100.0, 110.0, 120.0]


def test_extract_series_ignores_other_pipelines(tmp_path):
    entries = [
        [_metric_entry("pipe_a", "row_count", 50), _metric_entry("pipe_b", "row_count", 999)],
    ]
    hist_dir = _write_snapshots(tmp_path, entries)
    from pipewatch.history import load_snapshots
    snaps = load_snapshots(hist_dir)
    series = _extract_series(snaps, "pipe_a", "row_count")
    assert series == [50.0]


# ---------------------------------------------------------------------------
# analyze_trend
# ---------------------------------------------------------------------------

def test_analyze_trend_insufficient_data(tmp_path):
    entries = [[_metric_entry("pipe_a", "latency", 1.0)]]
    hist_dir = _write_snapshots(tmp_path, entries)
    result = analyze_trend("pipe_a", "latency", hist_dir, min_samples=3)
    assert result.direction == "insufficient_data"
    assert result.sample_count == 1


def test_analyze_trend_stable(tmp_path):
    entries = [
        [_metric_entry("pipe_a", "latency", 1.00)],
        [_metric_entry("pipe_a", "latency", 1.01)],
        [_metric_entry("pipe_a", "latency", 1.02)],
    ]
    hist_dir = _write_snapshots(tmp_path, entries)
    result = analyze_trend("pipe_a", "latency", hist_dir, threshold_pct=5.0)
    assert result.direction == "stable"


def test_analyze_trend_degrading(tmp_path):
    entries = [
        [_metric_entry("pipe_a", "latency", 1.0)],
        [_metric_entry("pipe_a", "latency", 1.5)],
        [_metric_entry("pipe_a", "latency", 2.0)],
    ]
    hist_dir = _write_snapshots(tmp_path, entries)
    result = analyze_trend("pipe_a", "latency", hist_dir, threshold_pct=5.0)
    assert result.direction == "degrading"
    assert result.delta == pytest.approx(1.0)


def test_analyze_trend_improving(tmp_path):
    entries = [
        [_metric_entry("pipe_a", "error_rate", 0.5)],
        [_metric_entry("pipe_a", "error_rate", 0.3)],
        [_metric_entry("pipe_a", "error_rate", 0.1)],
    ]
    hist_dir = _write_snapshots(tmp_path, entries)
    result = analyze_trend("pipe_a", "error_rate", hist_dir, threshold_pct=5.0)
    assert result.direction == "improving"


# ---------------------------------------------------------------------------
# summarize_trends
# ---------------------------------------------------------------------------

def test_summarize_trends_counts_correctly():
    trends = [
        TrendResult("p", "m", "improving", 1.0, 0.5, 3, -0.5),
        TrendResult("p", "n", "degrading", 1.0, 2.0, 3, 1.0),
        TrendResult("p", "o", "stable", 1.0, 1.0, 3, 0.0),
        TrendResult("p", "q", "stable", 1.0, 1.0, 3, 0.0),
    ]
    summary = summarize_trends(trends)
    assert summary["improving"] == 1
    assert summary["degrading"] == 1
    assert summary["stable"] == 2
    assert summary["insufficient_data"] == 0
