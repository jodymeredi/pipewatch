"""Integration tests: healthcheck interacting with metrics & dispatch simulation."""

from __future__ import annotations

import pytest

import pipewatch.healthcheck as hc
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset():
    hc._registry.clear()
    hc._heartbeats.clear()
    yield
    hc._registry.clear()
    hc._heartbeats.clear()


def _make_metric(pipeline: str, value: float = 1.0) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        metric="row_count",
        value=value,
        status="ok",
        tags={},
    )


def test_stale_pipelines_identified_from_check_all(monkeypatch):
    hc.register_healthcheck("etl-daily", tolerance_seconds=120)
    hc.register_healthcheck("etl-hourly", tolerance_seconds=120)

    monkeypatch.setattr(hc, "_now", lambda: 1_000_000.0)
    hc.record_heartbeat("etl-hourly")  # only hourly is alive

    monkeypatch.setattr(hc, "_now", lambda: 1_000_000.0 + 130)
    results = hc.check_all()

    stale = [r["pipeline"] for r in results if not r["healthy"]]
    healthy = [r["pipeline"] for r in results if r["healthy"]]

    assert "etl-daily" in stale
    assert "etl-hourly" in stale   # heartbeat also expired


def test_all_healthy_when_heartbeats_fresh(monkeypatch):
    for name in ("pipe-a", "pipe-b", "pipe-c"):
        hc.register_healthcheck(name, tolerance_seconds=300)

    monkeypatch.setattr(hc, "_now", lambda: 2_000_000.0)
    for name in ("pipe-a", "pipe-b", "pipe-c"):
        hc.record_heartbeat(name)

    results = hc.check_all()
    assert all(r["healthy"] for r in results)


def test_dispatch_simulation_skips_unhealthy_pipelines(monkeypatch):
    """Simulate a dispatch loop that skips pipelines failing health checks."""
    hc.register_healthcheck("pipe-ok", tolerance_seconds=60)
    hc.register_healthcheck("pipe-stale", tolerance_seconds=60)

    monkeypatch.setattr(hc, "_now", lambda: 5_000_000.0)
    hc.record_heartbeat("pipe-ok")
    # pipe-stale never gets a heartbeat

    metrics = [_make_metric("pipe-ok"), _make_metric("pipe-stale")]

    dispatched = []
    for m in metrics:
        health = hc.is_healthy(m.pipeline)
        if health is False:  # registered but stale
            continue
        dispatched.append(m.pipeline)

    assert "pipe-ok" in dispatched
    assert "pipe-stale" not in dispatched


def test_unregistered_pipeline_not_blocked_by_healthcheck():
    """A pipeline with no health-check registration is never blocked (None)."""
    result = hc.is_healthy("unregistered-pipe")
    assert result is None
    # In a dispatch simulation None means 'no opinion' → allow
    assert result is not False
