"""Integration tests: checkpoints interact with metrics and history."""

from __future__ import annotations

import time
import pytest

import pipewatch.checkpoint as cp
from pipewatch.metrics import collect_metric


@pytest.fixture(autouse=True)
def reset():
    cp._registry.clear()
    yield
    cp._registry.clear()


def _make_metric(pipeline: str, value: float, status: str = "ok"):
    return collect_metric(pipeline, value, status=status)


def _record_stages(pipeline: str, *stages: str) -> None:
    """Helper: record multiple checkpoints for a pipeline in one call."""
    for stage in stages:
        cp.record_checkpoint(pipeline, stage)


def test_checkpoint_recorded_before_metric_collection():
    """A checkpoint should be recordable independently of metric collection."""
    cp.record_checkpoint("orders", "extract")
    metric = _make_metric("orders", 42.0)
    assert metric.pipeline == "orders"
    ts = cp.get_checkpoint("orders", "extract")
    assert ts is not None and ts <= time.time()


def test_multiple_pipelines_independent_checkpoints():
    cp.record_checkpoint("orders", "extract")
    cp.record_checkpoint("inventory", "load")
    assert cp.get_checkpoint("orders", "extract") is not None
    assert cp.get_checkpoint("inventory", "load") is not None
    assert cp.get_checkpoint("orders", "load") is None
    assert cp.get_checkpoint("inventory", "extract") is None


def test_stale_detection_after_simulated_delay(monkeypatch):
    cp.record_checkpoint("billing", "transform")
    # Simulate time passing beyond the allowed window
    frozen = time.time() + 600
    monkeypatch.setattr(cp, "_now", lambda: frozen)
    assert cp.is_stale("billing", "transform", max_age_seconds=300) is True


def test_clear_pipeline_after_successful_run():
    """After a pipeline finishes, operator clears its checkpoints."""
    _record_stages("etl", "extract", "transform", "load")
    removed = cp.clear_pipeline("etl")
    assert removed == 3
    assert cp.list_checkpoints("etl") == []


def test_re_record_checkpoint_updates_timestamp(monkeypatch):
    base = time.time()
    monkeypatch.setattr(cp, "_now", lambda: base)
    cp.record_checkpoint("etl", "extract")

    later = base + 120
    monkeypatch.setattr(cp, "_now", lambda: later)
    cp.record_checkpoint("etl", "extract")

    assert cp.get_checkpoint("etl", "extract") == later


def test_list_checkpoints_returns_all_recorded_stages():
    """list_checkpoints should return every stage recorded for a pipeline."""
    _record_stages("reports", "extract", "transform", "validate", "load")
    stages = cp.list_checkpoints("reports")
    assert sorted(stages) == ["extract", "load", "transform", "validate"]
