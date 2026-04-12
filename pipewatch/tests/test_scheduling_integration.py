"""Integration tests: scheduling + metrics + history interaction."""

from __future__ import annotations

import datetime
import json
import pathlib
import tempfile

import pytest

import pipewatch.scheduling as sched
import pipewatch.history as hist
import pipewatch.metrics as metrics


@pytest.fixture(autouse=True)
def reset(tmp_path, monkeypatch):
    sched._schedules.clear()
    monkeypatch.setattr(hist, "_history_path", lambda name: tmp_path / f"{name}.jsonl")
    yield
    sched._schedules.clear()


def _make_metric(name: str, value: float = 1.0) -> metrics.PipelineMetric:
    return metrics.collect_metric(name, value)


def _last_run_from_history(pipeline: str) -> datetime.datetime | None:
    """Read the most recent recorded_at timestamp for *pipeline* from history."""
    path = hist._history_path(pipeline)
    if not path.exists():
        return None
    lines = path.read_text().strip().splitlines()
    if not lines:
        return None
    last = json.loads(lines[-1])
    ts = last.get("recorded_at")
    if ts is None:
        return None
    return datetime.datetime.fromisoformat(ts)


def test_pipeline_not_overdue_after_recent_snapshot():
    """A pipeline recorded recently should not appear overdue."""
    sched.set_schedule("etl_load", 3600)
    m = _make_metric("etl_load", 42.0)
    hist.record_snapshot("etl_load", [m])

    last_run = _last_run_from_history("etl_load")
    assert last_run is not None
    assert sched.is_overdue("etl_load", last_run) is False


def test_pipeline_overdue_when_no_history():
    """A scheduled pipeline with no recorded snapshots is overdue."""
    sched.set_schedule("etl_load", 3600)
    last_run = _last_run_from_history("etl_load")
    assert last_run is None
    assert sched.is_overdue("etl_load", last_run) is True


def test_overdue_pipelines_bulk_check():
    """overdue_pipelines correctly identifies mixed overdue state."""
    sched.set_schedule("fresh_pipe", 3600)
    sched.set_schedule("stale_pipe", 3600)

    m = _make_metric("fresh_pipe", 1.0)
    hist.record_snapshot("fresh_pipe", [m])

    last_runs = {
        "fresh_pipe": _last_run_from_history("fresh_pipe"),
        "stale_pipe": _last_run_from_history("stale_pipe"),
    }

    overdue = sched.overdue_pipelines(last_runs)
    assert "stale_pipe" in overdue
    assert "fresh_pipe" not in overdue


def test_schedule_removed_no_longer_tracked():
    """Removing a schedule means the pipeline is never reported overdue."""
    sched.set_schedule("etl_load", 3600)
    sched.remove_schedule("etl_load")
    assert sched.is_overdue("etl_load", None) is False
    assert sched.overdue_pipelines({"etl_load": None}) == []
