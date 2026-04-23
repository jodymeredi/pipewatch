"""Integration tests: capping applied before threshold evaluation."""

from __future__ import annotations

import pytest

import pipewatch.capping as capping
from pipewatch.metrics import PipelineMetric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    capping._registry.clear()
    yield
    capping._registry.clear()


def _make_metric(pipeline: str, value: float, warn: float = 80.0, crit: float = 90.0) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        value=value,
        warn_threshold=warn,
        crit_threshold=crit,
    )


def test_capping_prevents_critical_breach_when_ceiling_applied():
    """A raw value of 110 would be CRITICAL, but ceiling=95 keeps it WARNING."""
    capping.set_cap("etl_load", floor=0.0, ceiling=95.0)
    raw_value = 110.0
    capped = capping.apply_cap("etl_load", raw_value)
    metric = _make_metric("etl_load", capped)
    results = evaluate_thresholds([metric])
    statuses = {r["pipeline"]: r["status"] for r in results}
    assert statuses["etl_load"] == "warning"


def test_capping_floor_raises_ok_to_warning():
    """A raw value of 5 would be OK, but floor=85 pushes it into WARNING."""
    capping.set_cap("etl_extract", floor=85.0)
    raw_value = 5.0
    capped = capping.apply_cap("etl_extract", raw_value)
    metric = _make_metric("etl_extract", capped)
    results = evaluate_thresholds([metric])
    statuses = {r["pipeline"]: r["status"] for r in results}
    assert statuses["etl_extract"] == "warning"


def test_uncapped_pipeline_evaluates_raw_value():
    """Pipelines with no cap rule use the raw value as-is."""
    metric = _make_metric("etl_transform", 95.0)
    results = evaluate_thresholds([metric])
    statuses = {r["pipeline"]: r["status"] for r in results}
    assert statuses["etl_transform"] == "critical"


def test_multiple_pipelines_capped_independently():
    capping.set_cap("pipe_alpha", ceiling=50.0)
    capping.set_cap("pipe_beta", floor=85.0)

    metrics = [
        _make_metric("pipe_alpha", capping.apply_cap("pipe_alpha", 200.0)),
        _make_metric("pipe_beta", capping.apply_cap("pipe_beta", 10.0)),
        _make_metric("pipe_gamma", 20.0),
    ]
    results = evaluate_thresholds(metrics)
    statuses = {r["pipeline"]: r["status"] for r in results}

    assert statuses["pipe_alpha"] == "ok"       # 200 clamped to 50 → ok
    assert statuses["pipe_beta"] == "warning"   # 10 raised to 85 → warning
    assert statuses["pipe_gamma"] == "ok"       # 20, no cap, ok
