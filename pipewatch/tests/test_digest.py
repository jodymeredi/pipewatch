"""Tests for pipewatch/digest.py"""

from __future__ import annotations

import datetime
import json
import pathlib
import pytest

from pipewatch.digest import (
    _window_start,
    collect_window_metrics,
    build_digest,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _write_snapshot(hist_dir: pathlib.Path, pipeline: str, value: float, ts: datetime.datetime) -> None:
    path = hist_dir / f"{pipeline}.jsonl"
    entry = {
        "pipeline": pipeline,
        "metric": metric,
        "value": value,
        "tags": {},
        "recorded_at": ts.isoformat(),
    }
    with path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


# ---------------------------------------------------------------------------
# _window_start
# ---------------------------------------------------------------------------

def test_window_start_daily_zeroes_time():
    ws = _window_start("daily")
    assert ws.hour == 0
    assert ws.minute == 0
    assert ws.second == 0


def test_window_start_hourly_zeroes_minutes():
    ws = _window_start("hourly")
    assert ws.minute == 0
    assert ws.second == 0


# ---------------------------------------------------------------------------
# collect_window_metrics
# ---------------------------------------------------------------------------

def test_collect_window_metrics_returns_recent(tmp_path):
    now = datetime.datetime.utcnow()
    _write_snapshot(tmp_path, "etl", "row_count", 100, now)
    entries = collect_window_metrics(str(tmp_path), "etl", period="daily")
    assert len(entries) == 1
    assert entries[0]["pipeline"] == "etl"


def test_collect_window_metrics_excludes_old(tmp_path):
    old = datetime.datetime.utcnow() - datetime.timedelta(days=2)
    _write_snapshot(tmp_path, "etl", "row_count", 50, old)
    entries = collect_window_metrics(str(tmp_path), "etl", period="daily")
    assert entries == []


def test_collect_window_metrics_empty_for_unknown_pipeline(tmp_path):
    entries = collect_window_metrics(str(tmp_path), "nonexistent", period="daily")
    assert entries == []


# ---------------------------------------------------------------------------
# build_digest
# ---------------------------------------------------------------------------

def test_build_digest_structure(tmp_path):
    now = datetime.datetime.utcnow()
    _write_snapshot(tmp_path, "pipe_a", "latency", 5.0, now)
    digest = build_digest(str(tmp_path), ["pipe_a"], thresholds={}, period="daily")
    assert "period" in digest
    assert "generated_at" in digest
    assert "pipe_a" in digest["pipelines"]


def test_build_digest_counts_samples(tmp_path):
    now = datetime.datetime.utcnow()
    for v in [1.0, 2.0, 3.0]:
        _write_snapshot(tmp_path, "pipe_b", "errors", v, now)
    digest = build_digest(str(tmp_path), ["pipe_b"], thresholds={}, period="daily")
    assert digest["pipelines"]["pipe_b"]["samples"] == 3


def test_build_digest_no_samples(tmp_path):
    digest = build_digest(str(tmp_path), ["empty_pipe"], thresholds={}, period="daily")
    assert digest["pipelines"]["empty_pipe"]["samples"] == 0
    assert digest["pipelines"]["empty_pipe"]["alerts"] == []
