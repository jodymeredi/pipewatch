"""Tests for pipewatch.anomaly."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from pipewatch.anomaly import (
    AnomalyResult,
    _compute_stats,
    detect_anomaly,
    detect_anomalies_bulk,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_snapshot(directory: str, metrics: list) -> None:
    """Append a snapshot file containing *metrics* to *directory*."""
    ts = datetime.now(timezone.utc).isoformat()
    payload = {"recorded_at": ts, "metrics": metrics}
    path = os.path.join(directory, f"snap_{ts.replace(':', '-')}.json")
    with open(path, "w") as fh:
        json.dump(payload, fh)


def _metric_entry(pipeline: str, value: float) -> dict:
    return {"pipeline": pipeline, "value": value, "status": "ok", "tags": {}}


# ---------------------------------------------------------------------------
# unit tests for _compute_stats
# ---------------------------------------------------------------------------

def test_compute_stats_empty():
    mean, stddev = _compute_stats([])
    assert mean == 0.0
    assert stddev == 0.0


def test_compute_stats_single_value():
    mean, stddev = _compute_stats([42.0])
    assert mean == 42.0
    assert stddev == 0.0


def test_compute_stats_known_values():
    mean, stddev = _compute_stats([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert abs(mean - 5.0) < 1e-9
    assert abs(stddev - 2.0) < 1e-9


# ---------------------------------------------------------------------------
# detect_anomaly
# ---------------------------------------------------------------------------

def test_detect_anomaly_returns_none_when_insufficient_history():
    with tempfile.TemporaryDirectory() as d:
        _write_snapshot(d, [_metric_entry("pipe_a", 10.0)])
        result = detect_anomaly("pipe_a", 10.0, history_dir=d, min_samples=5)
    assert result is None


def test_detect_anomaly_returns_result_with_enough_history():
    with tempfile.TemporaryDirectory() as d:
        for v in [10.0, 10.5, 9.8, 10.2, 10.1]:
            _write_snapshot(d, [_metric_entry("pipe_a", v)])
        result = detect_anomaly("pipe_a", 10.3, history_dir=d, min_samples=5)
    assert isinstance(result, AnomalyResult)
    assert result.pipeline == "pipe_a"
    assert result.is_anomaly is False


def test_detect_anomaly_flags_outlier():
    with tempfile.TemporaryDirectory() as d:
        for v in [10.0, 10.0, 10.0, 10.0, 10.0]:
            _write_snapshot(d, [_metric_entry("pipe_a", v)])
        # current value is far from the mean of 10
        result = detect_anomaly("pipe_a", 99.0, history_dir=d, z_threshold=2.5)
    assert result is not None
    assert result.is_anomaly is True
    assert result.z_score == 0.0  # stddev is 0 → z_score clamped to 0; not flagged
    # When stddev is 0, z_score is 0 regardless of value — document this edge case
    assert result.is_anomaly is False  # z_score 0 < threshold 2.5


def test_detect_anomaly_as_dict_is_serialisable():
    with tempfile.TemporaryDirectory() as d:
        for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
            _write_snapshot(d, [_metric_entry("pipe_b", v)])
        result = detect_anomaly("pipe_b", 6.0, history_dir=d)
    assert result is not None
    d_out = result.as_dict()
    assert json.dumps(d_out)  # must not raise
    assert d_out["pipeline"] == "pipe_b"


# ---------------------------------------------------------------------------
# detect_anomalies_bulk
# ---------------------------------------------------------------------------

def test_detect_anomalies_bulk_skips_insufficient():
    with tempfile.TemporaryDirectory() as d:
        _write_snapshot(d, [_metric_entry("pipe_x", 5.0)])
        metrics = [{"pipeline": "pipe_x", "value": 5.0, "tags": {}}]
        results = detect_anomalies_bulk(metrics, history_dir=d, min_samples=5)
    assert results == []


def test_detect_anomalies_bulk_returns_results_for_multiple_pipelines():
    with tempfile.TemporaryDirectory() as d:
        for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
            _write_snapshot(d, [
                _metric_entry("alpha", v),
                _metric_entry("beta", v * 2),
            ])
        metrics = [
            {"pipeline": "alpha", "value": 3.0, "tags": {}},
            {"pipeline": "beta", "value": 6.0, "tags": {}},
        ]
        results = detect_anomalies_bulk(metrics, history_dir=d)
    assert len(results) == 2
    pipelines = {r.pipeline for r in results}
    assert "alpha" in pipelines
    assert "beta" in pipelines
