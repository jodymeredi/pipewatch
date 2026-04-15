"""Tests for pipewatch.watchdog."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import pipewatch.watchdog as wd


@pytest.fixture(autouse=True)
def reset_registry():
    wd._registry.clear()
    yield
    wd._registry.clear()


# ---------------------------------------------------------------------------
# set_watchdog
# ---------------------------------------------------------------------------

def test_set_watchdog_returns_dict():
    rule = wd.set_watchdog("pipeline_a", 300)
    assert rule["pipeline"] == "pipeline_a"
    assert rule["max_silence_seconds"] == 300
    assert rule["label"] == ""


def test_set_watchdog_with_label():
    rule = wd.set_watchdog("pipeline_b", 600, label="nightly ETL")
    assert rule["label"] == "nightly ETL"


def test_set_watchdog_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        wd.set_watchdog("  ", 300)


def test_set_watchdog_zero_silence_raises():
    with pytest.raises(ValueError, match="positive"):
        wd.set_watchdog("pipeline_a", 0)


def test_set_watchdog_negative_silence_raises():
    with pytest.raises(ValueError, match="positive"):
        wd.set_watchdog("pipeline_a", -10)


def test_set_watchdog_overwrites_previous():
    wd.set_watchdog("pipeline_a", 300)
    wd.set_watchdog("pipeline_a", 900)
    assert wd.get_watchdog("pipeline_a")["max_silence_seconds"] == 900


# ---------------------------------------------------------------------------
# remove / get / list
# ---------------------------------------------------------------------------

def test_remove_watchdog_returns_true_when_present():
    wd.set_watchdog("pipeline_a", 300)
    assert wd.remove_watchdog("pipeline_a") is True


def test_remove_watchdog_returns_false_when_absent():
    assert wd.remove_watchdog("nonexistent") is False


def test_get_watchdog_returns_none_when_missing():
    assert wd.get_watchdog("missing") is None


def test_list_watchdogs_returns_all():
    wd.set_watchdog("pipeline_a", 300)
    wd.set_watchdog("pipeline_b", 600)
    names = {r["pipeline"] for r in wd.list_watchdogs()}
    assert names == {"pipeline_a", "pipeline_b"}


def test_list_watchdogs_returns_copies():
    wd.set_watchdog("pipeline_a", 300)
    listing = wd.list_watchdogs()
    listing[0]["max_silence_seconds"] = 9999
    assert wd.get_watchdog("pipeline_a")["max_silence_seconds"] == 300


# ---------------------------------------------------------------------------
# check_watchdogs
# ---------------------------------------------------------------------------

def _write_snapshot(directory: str, pipeline: str, recorded_at: datetime) -> None:
    entry = {
        "recorded_at": recorded_at.isoformat(),
        "metrics": [{"pipeline": pipeline, "value": 1.0, "status": "ok"}],
    }
    ts = recorded_at.strftime("%Y%m%dT%H%M%S")
    path = Path(directory) / f"snapshot_{ts}_{pipeline}.jsonl"
    with path.open("a") as fh:
        fh.write(json.dumps(entry) + "\n")


def test_check_watchdogs_stale_when_no_history():
    wd.set_watchdog("pipeline_a", 300)
    with tempfile.TemporaryDirectory() as tmpdir:
        results = wd.check_watchdogs(history_dir=tmpdir)
    assert len(results) == 1
    assert results[0]["stale"] is True
    assert results[0]["last_seen"] is None


def test_check_watchdogs_not_stale_when_recent():
    wd.set_watchdog("pipeline_a", 3600)
    now = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_snapshot(tmpdir, "pipeline_a", now - timedelta(seconds=60))
        results = wd.check_watchdogs(history_dir=tmpdir)
    assert results[0]["stale"] is False


def test_check_watchdogs_stale_when_too_old():
    wd.set_watchdog("pipeline_a", 300)
    now = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_snapshot(tmpdir, "pipeline_a", now - timedelta(seconds=400))
        results = wd.check_watchdogs(history_dir=tmpdir)
    assert results[0]["stale"] is True


def test_check_watchdogs_ignores_other_pipelines():
    wd.set_watchdog("pipeline_a", 3600)
    now = datetime.now(timezone.utc)
    with tempfile.TemporaryDirectory() as tmpdir:
        _write_snapshot(tmpdir, "pipeline_b", now - timedelta(seconds=60))
        results = wd.check_watchdogs(history_dir=tmpdir)
    # pipeline_b snapshot should not count for pipeline_a
    assert results[0]["stale"] is True
