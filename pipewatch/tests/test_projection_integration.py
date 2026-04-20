"""Integration tests for pipewatch.projection against recorded history."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from pipewatch.history import record_snapshot
from pipewatch.metrics import PipelineMetric
from pipewatch.projection import project_pipeline, project_bulk, as_dict


def _make_metric(pipeline: str, value: float) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        value=value,
        status="ok",
        tags={},
        thresholds={},
    )


def _record_series(
    hist_dir: str,
    pipeline: str,
    values: list[float],
    interval_minutes: int = 5,
) -> None:
    base = datetime(2024, 5, 1, 8, 0, 0, tzinfo=timezone.utc)
    for i, v in enumerate(values):
        ts = base + timedelta(minutes=i * interval_minutes)
        metric = _make_metric(pipeline, v)
        record_snapshot([metric], history_dir=hist_dir, recorded_at=ts.isoformat())


# ---------------------------------------------------------------------------

def test_projection_over_recorded_history():
    with tempfile.TemporaryDirectory() as d:
        _record_series(d, "etl_load", [10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0])
        result = project_pipeline("etl_load", d, horizon=3)
    assert result.pipeline == "etl_load"
    assert result.projected_value is not None
    assert result.current_value is not None
    assert result.confidence is not None
    assert result.status in {"ok", "rising", "falling", "insufficient_data"}


def test_projection_result_as_dict_json_serialisable():
    with tempfile.TemporaryDirectory() as d:
        _record_series(d, "pipe_x", [5.0] * 8)
        result = project_pipeline("pipe_x", d, horizon=2)
    d_out = as_dict(result)
    assert json.dumps(d_out)  # no TypeError


def test_bulk_projection_multiple_pipelines():
    with tempfile.TemporaryDirectory() as d:
        _record_series(d, "alpha", [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0])
        _record_series(d, "beta", [100.0] * 8)
        results = project_bulk(["alpha", "beta"], d, horizon=4)
    assert len(results) == 2
    by_name = {r.pipeline: r for r in results}
    assert by_name["alpha"].status in {"rising", "ok"}
    assert by_name["beta"].status == "ok"


def test_projection_horizon_affects_predicted_value():
    with tempfile.TemporaryDirectory() as d:
        _record_series(d, "slope_pipe", [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0])
        r_short = project_pipeline("slope_pipe", d, horizon=1)
        r_long = project_pipeline("slope_pipe", d, horizon=10)
    if r_short.projected_value is not None and r_long.projected_value is not None:
        assert r_long.projected_value > r_short.projected_value
