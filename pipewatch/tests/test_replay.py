"""Tests for pipewatch.replay."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from pipewatch.replay import (
    ReplayResult,
    as_dict,
    replay_snapshots,
    summarize_replay,
)


def _write_snapshot(directory: str, metrics: list[dict], recorded_at: str) -> None:
    entry = {"recorded_at": recorded_at, "metrics": metrics}
    path = os.path.join(directory, f"{recorded_at.replace(':', '-')}.jsonl")
    with open(path, "a") as fh:
        fh.write(json.dumps(entry) + "\n")


def _metric_entry(pipeline: str, value: float) -> dict:
    return {"pipeline": pipeline, "value": value, "unit": "rows", "tags": {}}


@pytest.fixture()
def hist_dir(tmp_path):
    return str(tmp_path)


# ---------------------------------------------------------------------------
# ReplayResult / as_dict
# ---------------------------------------------------------------------------

def test_replay_result_fields():
    r = ReplayResult(pipeline="p", snapshot_time="t", status="ok")
    assert r.pipeline == "p"
    assert r.snapshot_time == "t"
    assert r.status == "ok"
    assert r.breaches == []
    assert r.alerts_dispatched == 0


def test_as_dict_serialisable():
    r = ReplayResult(pipeline="pipe", snapshot_time="2024-01-01T00:00:00Z", status="ok")
    d = as_dict(r)
    assert d["pipeline"] == "pipe"
    assert d["status"] == "ok"
    assert isinstance(d["breaches"], list)
    assert d["alerts_dispatched"] == 0


# ---------------------------------------------------------------------------
# replay_snapshots — dry_run=True (no actual dispatch)
# ---------------------------------------------------------------------------

def test_replay_returns_result_per_metric_entry(hist_dir):
    _write_snapshot(hist_dir, [_metric_entry("alpha", 10.0), _metric_entry("beta", 5.0)], "2024-01-01T10:00:00Z")
    results = replay_snapshots(hist_dir, dry_run=True)
    pipelines = [r.pipeline for r in results]
    assert "alpha" in pipelines
    assert "beta" in pipelines


def test_replay_filters_by_pipeline(hist_dir):
    _write_snapshot(hist_dir, [_metric_entry("alpha", 10.0), _metric_entry("beta", 5.0)], "2024-01-01T10:00:00Z")
    results = replay_snapshots(hist_dir, pipeline="alpha", dry_run=True)
    assert all(r.pipeline == "alpha" for r in results)
    assert len(results) == 1


def test_replay_dry_run_does_not_dispatch(hist_dir):
    _write_snapshot(hist_dir, [_metric_entry("alpha", 999.0)], "2024-01-01T10:00:00Z")
    results = replay_snapshots(hist_dir, dry_run=True)
    assert all(r.alerts_dispatched == 0 for r in results)


def test_replay_empty_history_returns_empty_list(hist_dir):
    results = replay_snapshots(hist_dir, dry_run=True)
    assert results == []


def test_replay_snapshot_time_recorded(hist_dir):
    ts = "2024-06-15T08:30:00Z"
    _write_snapshot(hist_dir, [_metric_entry("gamma", 1.0)], ts)
    results = replay_snapshots(hist_dir, dry_run=True)
    assert results[0].snapshot_time == ts


# ---------------------------------------------------------------------------
# summarize_replay
# ---------------------------------------------------------------------------

def test_summarize_replay_all_ok():
    results = [ReplayResult(pipeline="p", snapshot_time="t", status="ok") for _ in range(3)]
    summary = summarize_replay(results)
    assert summary == {"total": 3, "ok": 3, "breaching": 0}


def test_summarize_replay_mixed():
    results = [
        ReplayResult(pipeline="p1", snapshot_time="t", status="ok"),
        ReplayResult(pipeline="p2", snapshot_time="t", status="warning"),
        ReplayResult(pipeline="p3", snapshot_time="t", status="critical"),
    ]
    summary = summarize_replay(results)
    assert summary["total"] == 3
    assert summary["ok"] == 1
    assert summary["breaching"] == 2


def test_summarize_replay_empty():
    assert summarize_replay([]) == {"total": 0, "ok": 0, "breaching": 0}
