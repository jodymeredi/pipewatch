"""Integration tests: watchdog + history.record_snapshot."""

from __future__ import annotations

import tempfile
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest

import pipewatch.watchdog as wd
from pipewatch.history import record_snapshot
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset():
    wd._registry.clear()
    yield
    wd._registry.clear()


def _make_metric(pipeline: str, status: str = "ok") -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        metric="row_count",
        value=100.0,
        status=status,
        tags={},
    )


def test_pipeline_not_stale_after_recent_snapshot():
    wd.set_watchdog("etl_daily", max_silence_seconds=3600)
    now = datetime.now(timezone.utc)

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pipewatch.history._history_path", return_value=tmpdir):
            record_snapshot([_make_metric("etl_daily")])
            results = wd.check_watchdogs(history_dir=tmpdir)

    assert len(results) == 1
    r = results[0]
    assert r["pipeline"] == "etl_daily"
    assert r["stale"] is False
    assert r["last_seen"] is not None


def test_pipeline_stale_with_no_snapshots():
    wd.set_watchdog("etl_hourly", max_silence_seconds=300)

    with tempfile.TemporaryDirectory() as tmpdir:
        results = wd.check_watchdogs(history_dir=tmpdir)

    assert results[0]["stale"] is True
    assert results[0]["elapsed_seconds"] is None


def test_multiple_pipelines_evaluated_independently():
    wd.set_watchdog("pipe_ok", max_silence_seconds=3600)
    wd.set_watchdog("pipe_stale", max_silence_seconds=60)
    now = datetime.now(timezone.utc)

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pipewatch.history._history_path", return_value=tmpdir):
            record_snapshot([_make_metric("pipe_ok")])
            results = wd.check_watchdogs(history_dir=tmpdir)

    by_name = {r["pipeline"]: r for r in results}
    assert by_name["pipe_ok"]["stale"] is False
    assert by_name["pipe_stale"]["stale"] is True


def test_elapsed_seconds_reported_correctly():
    wd.set_watchdog("etl_daily", max_silence_seconds=3600)
    now = datetime.now(timezone.utc)

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("pipewatch.history._history_path", return_value=tmpdir):
            record_snapshot([_make_metric("etl_daily")])
            results = wd.check_watchdogs(history_dir=tmpdir)

    r = results[0]
    assert r["elapsed_seconds"] is not None
    assert r["elapsed_seconds"] < 10  # recorded just moments ago
