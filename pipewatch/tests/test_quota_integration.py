"""Integration tests: quota interacting with dispatch simulation."""

from __future__ import annotations

from typing import List

import pytest

import pipewatch.quota as quota_mod
from pipewatch.quota import is_quota_exceeded, record_alert, remaining, set_quota
from pipewatch.metrics import PipelineMetric, collect_metric


@pytest.fixture(autouse=True)
def reset():
    quota_mod._registry.clear()
    quota_mod._counts.clear()
    yield
    quota_mod._registry.clear()
    quota_mod._counts.clear()


def _make_metric(pipeline: str, status: str = "warning") -> PipelineMetric:
    return collect_metric(pipeline, value=42.0, status=status)


def _simulate_dispatch(metrics: List[PipelineMetric]) -> List[str]:
    """Return pipeline names that were allowed through (quota not exceeded)."""
    dispatched = []
    for m in metrics:
        if not is_quota_exceeded(m.pipeline):
            dispatched.append(m.pipeline)
            record_alert(m.pipeline)
    return dispatched


def test_dispatch_respects_quota():
    set_quota("etl_load", max_alerts=2, window_seconds=3600)
    metrics = [_make_metric("etl_load")] * 5
    dispatched = _simulate_dispatch(metrics)
    assert len(dispatched) == 2


def test_dispatch_allowed_when_quota_not_exceeded():
    set_quota("etl_load", max_alerts=10, window_seconds=3600)
    metrics = [_make_metric("etl_load")] * 3
    dispatched = _simulate_dispatch(metrics)
    assert len(dispatched) == 3


def test_pipeline_without_quota_always_dispatched():
    metrics = [_make_metric("free_pipe")] * 10
    dispatched = _simulate_dispatch(metrics)
    assert len(dispatched) == 10


def test_remaining_tracks_across_multiple_dispatches():
    set_quota("pipe", max_alerts=5, window_seconds=3600)
    for _ in range(3):
        record_alert("pipe")
    assert remaining("pipe") == 2


def test_multiple_pipelines_independent_quotas():
    set_quota("pipe_a", max_alerts=1, window_seconds=3600)
    set_quota("pipe_b", max_alerts=3, window_seconds=3600)
    metrics = [_make_metric("pipe_a")] * 3 + [_make_metric("pipe_b")] * 3
    dispatched = _simulate_dispatch(metrics)
    a_count = dispatched.count("pipe_a")
    b_count = dispatched.count("pipe_b")
    assert a_count == 1
    assert b_count == 3
