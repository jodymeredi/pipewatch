"""Integration tests: forecast over history recorded via record_snapshot."""
import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from pipewatch.history import record_snapshot
from pipewatch.metrics import PipelineMetric
from pipewatch.forecast import forecast_pipeline, forecast_bulk


# ---------------------------------------------------------------------------
# fixtures / helpers
# ---------------------------------------------------------------------------

def _make_metric(pipeline: str, value: float) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        name="row_count",
        value=value,
        status="ok",
        tags={},
    )


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_forecast_over_recorded_history():
    """forecast_pipeline works against snapshots written by record_snapshot."""
    with tempfile.TemporaryDirectory() as d:
        for i in range(6):
            record_snapshot([_make_metric("etl_main", float(i * 5))], history_dir=d)
        result = forecast_pipeline("etl_main", "row_count", horizon=1, history_dir=d)
    assert result is not None
    assert result.pipeline == "etl_main"
    assert result.predicted_value == pytest.approx(30.0)
    assert result.data_points == 6


def test_forecast_bulk_over_multiple_pipelines():
    with tempfile.TemporaryDirectory() as d:
        for i in range(5):
            metrics = [
                _make_metric("pipe_x", float(i)),
                _make_metric("pipe_y", float(i * 2)),
            ]
            record_snapshot(metrics, history_dir=d)
        results = forecast_bulk(["pipe_x", "pipe_y"], "row_count", horizon=2, history_dir=d)
    assert len(results) == 2
    names = {r.pipeline for r in results}
    assert names == {"pipe_x", "pipe_y"}


def test_forecast_horizon_affects_predicted_value():
    """Larger horizon should produce a larger predicted value for rising data."""
    with tempfile.TemporaryDirectory() as d:
        for i in range(6):
            record_snapshot([_make_metric("pipe_z", float(i))], history_dir=d)
        r1 = forecast_pipeline("pipe_z", "row_count", horizon=1, history_dir=d)
        r2 = forecast_pipeline("pipe_z", "row_count", horizon=5, history_dir=d)
    assert r1 is not None and r2 is not None
    assert r2.predicted_value > r1.predicted_value
