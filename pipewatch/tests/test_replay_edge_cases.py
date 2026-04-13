"""Edge-case tests for pipewatch.replay."""

from __future__ import annotations

import json
import os

import pytest

from pipewatch.replay import replay_snapshots, summarize_replay, ReplayResult, as_dict


@pytest.fixture()
def hist_dir(tmp_path):
    return str(tmp_path)


def _raw_entry(directory: str, payload: dict) -> None:
    path = os.path.join(directory, "snap.jsonl")
    with open(path, "a") as fh:
        fh.write(json.dumps(payload) + "\n")


def test_entry_missing_metrics_key_does_not_crash(hist_dir):
    """Snapshot entries without a 'metrics' key are skipped gracefully."""
    _raw_entry(hist_dir, {"recorded_at": "2024-01-01T00:00:00Z"})
    results = replay_snapshots(hist_dir, dry_run=True)
    assert results == []


def test_metric_missing_pipeline_key_uses_empty_string(hist_dir):
    """Metrics without 'pipeline' fall back to empty string and are still processed."""
    _raw_entry(
        hist_dir,
        {"recorded_at": "2024-01-01T00:00:00Z", "metrics": [{"value": 5.0, "unit": "rows"}]},
    )
    results = replay_snapshots(hist_dir, dry_run=True)
    assert len(results) == 1
    assert results[0].pipeline == ""


def test_pipeline_filter_no_match_returns_empty(hist_dir):
    _raw_entry(
        hist_dir,
        {"recorded_at": "2024-01-01T00:00:00Z", "metrics": [{"pipeline": "alpha", "value": 1.0}]},
    )
    results = replay_snapshots(hist_dir, pipeline="nonexistent", dry_run=True)
    assert results == []


def test_as_dict_contains_all_keys():
    r = ReplayResult(
        pipeline="x",
        snapshot_time="2024-01-01T00:00:00Z",
        status="warning",
        breaches=[{"level": "warning"}],
        alerts_dispatched=0,
    )
    d = as_dict(r)
    for key in ("pipeline", "snapshot_time", "status", "breaches", "alerts_dispatched"):
        assert key in d


def test_summarize_replay_single_breaching():
    results = [ReplayResult(pipeline="p", snapshot_time="t", status="critical")]
    s = summarize_replay(results)
    assert s["total"] == 1
    assert s["ok"] == 0
    assert s["breaching"] == 1


def test_replay_multiple_metrics_same_snapshot(hist_dir):
    """Multiple metrics in one snapshot each produce their own ReplayResult."""
    entry = {
        "recorded_at": "2024-03-10T12:00:00Z",
        "metrics": [
            {"pipeline": "a", "value": 1.0, "unit": "rows", "tags": {}},
            {"pipeline": "b", "value": 2.0, "unit": "rows", "tags": {}},
            {"pipeline": "c", "value": 3.0, "unit": "rows", "tags": {}},
        ],
    }
    _raw_entry(hist_dir, entry)
    results = replay_snapshots(hist_dir, dry_run=True)
    assert len(results) == 3
    assert {r.pipeline for r in results} == {"a", "b", "c"}
