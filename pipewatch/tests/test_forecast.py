"""Unit tests for pipewatch.forecast."""
import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from pipewatch.forecast import (
    ForecastResult,
    as_dict,
    _linear_fit,
    _confidence,
    forecast_pipeline,
    forecast_bulk,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_snapshots(directory: str, entries_per_snap: list[list[dict]]):
    """Write one NDJSON snapshot file with multiple snapshot lines."""
    path = os.path.join(directory, "snap.jsonl")
    with open(path, "w") as fh:
        for metrics in entries_per_snap:
            fh.write(json.dumps({"recorded_at": datetime.now(timezone.utc).isoformat(), "metrics": metrics}) + "\n")


def _metric_entry(pipeline: str, name: str, value: float) -> dict:
    return {"pipeline": pipeline, "name": name, "value": value, "status": "ok"}


# ---------------------------------------------------------------------------
# _linear_fit
# ---------------------------------------------------------------------------

def test_linear_fit_flat_series():
    slope, intercept = _linear_fit([5.0, 5.0, 5.0, 5.0])
    assert slope == pytest.approx(0.0)
    assert intercept == pytest.approx(5.0)


def test_linear_fit_rising_series():
    slope, intercept = _linear_fit([0.0, 1.0, 2.0, 3.0])
    assert slope == pytest.approx(1.0)
    assert intercept == pytest.approx(0.0)


def test_linear_fit_single_value():
    slope, intercept = _linear_fit([7.0])
    assert slope == pytest.approx(0.0)
    assert intercept == pytest.approx(7.0)


# ---------------------------------------------------------------------------
# _confidence
# ---------------------------------------------------------------------------

def test_confidence_low():
    assert _confidence(2) == "low"
    assert _confidence(7) == "low"


def test_confidence_medium():
    assert _confidence(8) == "medium"
    assert _confidence(19) == "medium"


def test_confidence_high():
    assert _confidence(20) == "high"
    assert _confidence(100) == "high"


# ---------------------------------------------------------------------------
# forecast_pipeline
# ---------------------------------------------------------------------------

def test_forecast_pipeline_insufficient_data():
    with tempfile.TemporaryDirectory() as d:
        _write_snapshots(d, [
            [_metric_entry("pipe_a", "row_count", 10)],
            [_metric_entry("pipe_a", "row_count", 20)],
        ])
        result = forecast_pipeline("pipe_a", "row_count", history_dir=d)
    assert result is None


def test_forecast_pipeline_returns_result():
    with tempfile.TemporaryDirectory() as d:
        snaps = [[_metric_entry("pipe_a", "row_count", float(i * 10))] for i in range(5)]
        _write_snapshots(d, snaps)
        result = forecast_pipeline("pipe_a", "row_count", horizon=1, history_dir=d)
    assert isinstance(result, ForecastResult)
    assert result.pipeline == "pipe_a"
    assert result.metric_name == "row_count"
    assert result.horizon == 1
    assert result.data_points == 5


def test_forecast_pipeline_predicted_value_correct():
    with tempfile.TemporaryDirectory() as d:
        # values 0,1,2,3,4 → slope=1, intercept=0 → predict at index 5 = 5
        snaps = [[_metric_entry("p", "v", float(i))] for i in range(5)]
        _write_snapshots(d, snaps)
        result = forecast_pipeline("p", "v", horizon=1, history_dir=d)
    assert result.predicted_value == pytest.approx(5.0)


def test_forecast_pipeline_ignores_other_pipelines():
    with tempfile.TemporaryDirectory() as d:
        snaps = [
            [_metric_entry("pipe_a", "v", float(i)), _metric_entry("pipe_b", "v", 999.0)]
            for i in range(5)
        ]
        _write_snapshots(d, snaps)
        result = forecast_pipeline("pipe_a", "v", history_dir=d)
    assert result is not None
    assert result.data_points == 5


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_serialisable():
    r = ForecastResult(
        pipeline="p", metric_name="m", horizon=2,
        predicted_value=42.1234, slope=0.5, intercept=1.0,
        confidence="medium", data_points=10,
    )
    d = as_dict(r)
    assert json.dumps(d)  # must not raise
    assert d["pipeline"] == "p"
    assert d["confidence"] == "medium"


# ---------------------------------------------------------------------------
# forecast_bulk
# ---------------------------------------------------------------------------

def test_forecast_bulk_returns_only_viable_pipelines():
    with tempfile.TemporaryDirectory() as d:
        snaps = [
            [
                _metric_entry("good", "v", float(i)),
                _metric_entry("bad", "v", float(i)),  # only 2 snaps for bad
            ]
            for i in range(5)
        ]
        # write 5 snaps for 'good', only 2 for 'bad' by trimming
        _write_snapshots(d, snaps[:2])  # both get 2 entries
        # overwrite with 5 entries for good only
        path = os.path.join(d, "snap.jsonl")
        with open(path, "w") as fh:
            for i in range(5):
                fh.write(json.dumps({"recorded_at": datetime.now(timezone.utc).isoformat(),
                                     "metrics": [_metric_entry("good", "v", float(i))]}) + "\n")
        results = forecast_bulk(["good", "bad"], "v", history_dir=d)
    assert len(results) == 1
    assert results[0].pipeline == "good"
