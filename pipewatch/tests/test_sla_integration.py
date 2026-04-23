"""Integration tests: SLA checks against real metric + history data."""

from __future__ import annotations

import datetime
import json
import pathlib

import pytest

import pipewatch.sla as sla_mod
from pipewatch.sla import set_sla, check_sla
from pipewatch.metrics import PipelineMetric
from pipewatch.history import record_snapshot


@pytest.fixture()
def reset(tmp_path, monkeypatch):
    sla_mod._registry.clear()
    import pipewatch.history as hist_mod
    monkeypatch.setattr(hist_mod, "_history_path", lambda: tmp_path / "history.jsonl")
    yield tmp_path
    sla_mod._registry.clear()


def _make_metric(name: str, value: float, status: str = "ok") -> PipelineMetric:
    return PipelineMetric(
        pipeline=name,
        metric="row_count",
        value=value,
        status=status,
        tags={},
    )


def test_sla_ok_when_snapshot_recorded_before_deadline(reset, monkeypatch):
    """A pipeline that ran before the deadline should pass SLA check."""
    metrics = [_make_metric("etl.orders", 1000)]
    record_snapshot(metrics)

    set_sla("etl.orders", "06:00", window_minutes=30)

    # Simulate current time just after deadline but pipeline ran at 05:50
    now = datetime.datetime(2024, 6, 1, 6, 10, 0)
    last_run = datetime.datetime(2024, 6, 1, 5, 50, 0)
    monkeypatch.setattr(sla_mod, "_utcnow", lambda: now)

    result = check_sla("etl.orders", last_run_utc=last_run)
    assert result["status"] == "ok"


def test_sla_breached_when_no_recent_run(reset, monkeypatch):
    """A pipeline with no last_run after deadline should be breached."""
    set_sla("etl.inventory", "04:00", window_minutes=15)

    now = datetime.datetime(2024, 6, 1, 5, 0, 0)  # well past deadline + window
    monkeypatch.setattr(sla_mod, "_utcnow", lambda: now)

    result = check_sla("etl.inventory", last_run_utc=None)
    assert result["status"] == "breached"


def test_multiple_pipelines_independent_slas(reset, monkeypatch):
    """Each pipeline's SLA is evaluated independently."""
    set_sla("pipe.a", "02:00", window_minutes=10)
    set_sla("pipe.b", "23:59", window_minutes=60)

    now = datetime.datetime(2024, 6, 1, 3, 0, 0)
    monkeypatch.setattr(sla_mod, "_utcnow", lambda: now)

    result_a = check_sla("pipe.a", last_run_utc=None)
    result_b = check_sla("pipe.b", last_run_utc=None)

    assert result_a["status"] == "breached"
    assert result_b["status"] == "ok"  # deadline not yet reached


def test_list_slas_after_bulk_registration(reset):
    """list_slas returns all registered rules."""
    pipelines = ["alpha", "beta", "gamma"]
    for p in pipelines:
        set_sla(p, "12:00")

    from pipewatch.sla import list_slas
    names = {r["pipeline"] for r in list_slas()}
    assert names == set(pipelines)
