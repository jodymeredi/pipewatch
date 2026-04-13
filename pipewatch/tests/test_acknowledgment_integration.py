"""Integration tests: acknowledgment interacts with metrics and alert dispatch."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import pipewatch.acknowledgment as ack_mod
from pipewatch.acknowledgment import acknowledge, is_acknowledged, clear_acknowledgment
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset():
    ack_mod._registry.clear()
    yield
    ack_mod._registry.clear()


def _make_metric(name: str, status: str = "critical") -> PipelineMetric:
    return PipelineMetric(
        pipeline=name,
        value=99.0,
        status=status,
        tags={},
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


def test_acknowledged_pipeline_skipped_in_dispatch_simulation():
    """Simulate alert dispatch that skips acknowledged pipelines."""
    metrics = [_make_metric("pipe_a"), _make_metric("pipe_b")]
    acknowledge("pipe_a", "critical", "ops-team")

    dispatched = [
        m.pipeline
        for m in metrics
        if not is_acknowledged(m.pipeline, m.status)
    ]
    assert "pipe_a" not in dispatched
    assert "pipe_b" in dispatched


def test_cleared_acknowledgment_pipeline_dispatched_again():
    metrics = [_make_metric("pipe_a")]
    acknowledge("pipe_a", "critical", "ops-team")
    clear_acknowledgment("pipe_a")

    dispatched = [
        m.pipeline
        for m in metrics
        if not is_acknowledged(m.pipeline, m.status)
    ]
    assert "pipe_a" in dispatched


def test_ok_status_not_blocked_by_critical_ack():
    """Acknowledging critical should not suppress ok-level alerts."""
    acknowledge("pipe_a", "critical", "ops-team")
    metric_ok = _make_metric("pipe_a", status="ok")
    assert is_acknowledged(metric_ok.pipeline, metric_ok.status) is False


def test_multiple_pipelines_independent_acknowledgments():
    acknowledge("pipe_a", "warning", "alice")
    acknowledge("pipe_b", "critical", "bob")
    assert is_acknowledged("pipe_a", "warning") is True
    assert is_acknowledged("pipe_b", "critical") is True
    clear_acknowledgment("pipe_a")
    assert is_acknowledged("pipe_a", "warning") is False
    assert is_acknowledged("pipe_b", "critical") is True
