"""Integration tests: snapshot_diff wired to history snapshots."""

import json
import pathlib
import tempfile
from datetime import datetime, timezone

import pytest

from pipewatch import history
from pipewatch.snapshot_diff import diff_snapshots, regressions, recoveries


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def hist_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "_history_path", lambda: tmp_path / "history.jsonl")
    return tmp_path


def _metric(pipeline: str, status: str, value: float = 0.0) -> dict:
    return {
        "pipeline": pipeline,
        "metric": "row_count",
        "value": value,
        "status": status,
        "tags": {},
    }


# ---------------------------------------------------------------------------
# helpers that read snapshots back as flat metric lists
# ---------------------------------------------------------------------------

def _snapshot_to_metrics(snapshot: dict) -> list:
    """history.record_snapshot stores {recorded_at, metrics:[...]}."""
    return snapshot.get("metrics", [])


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------

def test_diff_across_two_recorded_snapshots(hist_dir):
    snap1 = [_metric("etl_load", "ok", 100.0), _metric("etl_transform", "ok", 50.0)]
    snap2 = [_metric("etl_load", "critical", 0.0), _metric("etl_transform", "ok", 55.0)]

    history.record_snapshot(snap1)
    history.record_snapshot(snap2)

    snapshots = history.load_snapshots()
    assert len(snapshots) == 2

    prev_metrics = _snapshot_to_metrics(snapshots[0])
    curr_metrics = _snapshot_to_metrics(snapshots[1])

    entries = diff_snapshots(prev_metrics, curr_metrics)
    reg = regressions(entries)
    rec = recoveries(entries)

    assert len(reg) == 1
    assert reg[0].pipeline == "etl_load"
    assert len(rec) == 0


def test_recovery_detected_across_snapshots(hist_dir):
    snap1 = [_metric("etl_load", "critical", 0.0)]
    snap2 = [_metric("etl_load", "ok", 200.0)]

    history.record_snapshot(snap1)
    history.record_snapshot(snap2)

    snapshots = history.load_snapshots()
    prev_metrics = _snapshot_to_metrics(snapshots[0])
    curr_metrics = _snapshot_to_metrics(snapshots[1])

    entries = diff_snapshots(prev_metrics, curr_metrics)
    rec = recoveries(entries)

    assert len(rec) == 1
    assert rec[0].pipeline == "etl_load"
    assert rec[0].previous_value == pytest.approx(0.0)
    assert rec[0].current_value == pytest.approx(200.0)


def test_no_changes_when_snapshots_identical(hist_dir):
    snap = [_metric("pipe_a", "ok", 10.0), _metric("pipe_b", "warning", 5.0)]
    history.record_snapshot(snap)
    history.record_snapshot(snap)

    snapshots = history.load_snapshots()
    prev_metrics = _snapshot_to_metrics(snapshots[0])
    curr_metrics = _snapshot_to_metrics(snapshots[1])

    entries = diff_snapshots(prev_metrics, curr_metrics)
    assert all(not e.changed for e in entries)
    assert regressions(entries) == []
    assert recoveries(entries) == []
