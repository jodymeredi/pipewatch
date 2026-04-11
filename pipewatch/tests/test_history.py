"""Tests for pipewatch.history — snapshot persistence."""

import json
from pathlib import Path

import pytest

from pipewatch.history import load_snapshots, purge_history, record_snapshot


@pytest.fixture()
def hist_dir(tmp_path: Path) -> Path:
    return tmp_path / "history"


@pytest.fixture()
def sample_metric() -> dict:
    return {
        "pipeline": "orders_etl",
        "value": 42.0,
        "unit": "rows",
        "status": "ok",
        "tags": {"env": "prod"},
    }


def test_record_snapshot_creates_file(hist_dir, sample_metric):
    path = record_snapshot("orders_etl", sample_metric, history_dir=hist_dir)
    assert path.exists()


def test_record_snapshot_appends_multiple_entries(hist_dir, sample_metric):
    for _ in range(3):
        record_snapshot("orders_etl", sample_metric, history_dir=hist_dir)
    snapshots = load_snapshots("orders_etl", history_dir=hist_dir)
    assert len(snapshots) == 3


def test_record_snapshot_entry_has_recorded_at(hist_dir, sample_metric):
    record_snapshot("orders_etl", sample_metric, history_dir=hist_dir)
    snapshots = load_snapshots("orders_etl", history_dir=hist_dir)
    assert "recorded_at" in snapshots[0]


def test_record_snapshot_entry_contains_metric_fields(hist_dir, sample_metric):
    record_snapshot("orders_etl", sample_metric, history_dir=hist_dir)
    entry = load_snapshots("orders_etl", history_dir=hist_dir)[0]
    assert entry["pipeline"] == "orders_etl"
    assert entry["value"] == 42.0
    assert entry["status"] == "ok"


def test_load_snapshots_returns_empty_for_unknown_pipeline(hist_dir):
    result = load_snapshots("nonexistent", history_dir=hist_dir)
    assert result == []


def test_load_snapshots_respects_limit(hist_dir, sample_metric):
    for _ in range(10):
        record_snapshot("orders_etl", sample_metric, history_dir=hist_dir)
    result = load_snapshots("orders_etl", history_dir=hist_dir, limit=4)
    assert len(result) == 4


def test_load_snapshots_returns_most_recent_entries(hist_dir):
    for i in range(5):
        record_snapshot("orders_etl", {"value": float(i)}, history_dir=hist_dir)
    result = load_snapshots("orders_etl", history_dir=hist_dir, limit=3)
    values = [e["value"] for e in result]
    assert values == [2.0, 3.0, 4.0]


def test_purge_history_removes_file(hist_dir, sample_metric):
    record_snapshot("orders_etl", sample_metric, history_dir=hist_dir)
    removed = purge_history("orders_etl", history_dir=hist_dir)
    assert removed is True
    assert load_snapshots("orders_etl", history_dir=hist_dir) == []


def test_purge_history_returns_false_when_no_file(hist_dir):
    assert purge_history("ghost_pipeline", history_dir=hist_dir) is False


def test_pipeline_name_with_spaces_is_safe(hist_dir, sample_metric):
    record_snapshot("my pipeline", sample_metric, history_dir=hist_dir)
    result = load_snapshots("my pipeline", history_dir=hist_dir)
    assert len(result) == 1
