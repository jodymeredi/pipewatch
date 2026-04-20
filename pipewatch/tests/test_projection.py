"""Unit tests for pipewatch.projection."""
from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from pipewatch.projection import (
    ProjectionResult,
    as_dict,
    project_pipeline,
    project_bulk,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _metric_entry(pipeline: str, value: float) -> dict:
    return {
        "pipeline": pipeline,
        "value": value,
        "status": "ok",
        "tags": {},
    }


def _write_snapshots(directory: str, entries: list[tuple[str, list[dict]]]) -> None:
    """Write multiple snapshot files into *directory*."""
    for i, (ts, metrics) in enumerate(entries):
        fname = os.path.join(directory, f"snap_{i:04d}.jsonl")
        with open(fname, "w") as fh:
            fh.write(json.dumps({"recorded_at": ts, "metrics": metrics}) + "\n")


def _ts(offset_seconds: int = 0) -> str:
    from datetime import timedelta
    base = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return (base + timedelta(seconds=offset_seconds)).isoformat()


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_serialisable():
    r = ProjectionResult(
        pipeline="p",
        current_value=10.0,
        projected_value=12.0,
        horizon_steps=3,
        trend_direction="up",
        pct_change=20.0,
        confidence=0.9,
        status="rising",
        notes=["note"],
    )
    d = as_dict(r)
    assert json.dumps(d)  # must be JSON-serialisable
    assert d["pipeline"] == "p"
    assert d["status"] == "rising"


# ---------------------------------------------------------------------------
# project_pipeline — insufficient data
# ---------------------------------------------------------------------------

def test_project_pipeline_insufficient_data():
    with tempfile.TemporaryDirectory() as d:
        result = project_pipeline("ghost", d, horizon=3)
    assert result.status == "insufficient_data"
    assert result.projected_value is None
    assert result.notes


# ---------------------------------------------------------------------------
# project_pipeline — rising trend
# ---------------------------------------------------------------------------

def test_project_pipeline_rising():
    with tempfile.TemporaryDirectory() as d:
        snaps = [
            (_ts(i * 60), [_metric_entry("pipe_a", float(10 + i * 5))])
            for i in range(8)
        ]
        _write_snapshots(d, snaps)
        result = project_pipeline("pipe_a", d, horizon=3, rising_threshold=5.0)
    assert result.status == "rising"
    assert result.projected_value is not None
    assert result.projected_value > result.current_value  # type: ignore[operator]


# ---------------------------------------------------------------------------
# project_pipeline — stable series
# ---------------------------------------------------------------------------

def test_project_pipeline_stable():
    with tempfile.TemporaryDirectory() as d:
        snaps = [
            (_ts(i * 60), [_metric_entry("pipe_b", 42.0)])
            for i in range(8)
        ]
        _write_snapshots(d, snaps)
        result = project_pipeline("pipe_b", d, horizon=3)
    assert result.status == "ok"
    assert result.pct_change == 0.0 or abs(result.pct_change or 0) < 1.0  # type: ignore[operator]


# ---------------------------------------------------------------------------
# project_bulk
# ---------------------------------------------------------------------------

def test_project_bulk_returns_one_per_pipeline():
    with tempfile.TemporaryDirectory() as d:
        results = project_bulk(["alpha", "beta", "gamma"], d, horizon=2)
    assert len(results) == 3
    names = {r.pipeline for r in results}
    assert names == {"alpha", "beta", "gamma"}


def test_project_bulk_all_serialisable():
    with tempfile.TemporaryDirectory() as d:
        results = project_bulk(["x", "y"], d)
    for r in results:
        json.dumps(as_dict(r))
