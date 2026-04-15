"""Integration tests: fingerprinting interacts with metrics evaluation."""

from __future__ import annotations

import pytest

import pipewatch.fingerprint as fp_mod
from pipewatch.fingerprint import register_fingerprint, list_fingerprints, reset_registry
from pipewatch.metrics import PipelineMetric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    fp_mod.reset_registry()
    yield
    fp_mod.reset_registry()


def _make_metric(pipeline: str, value: float, warn: float, crit: float) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        value=value,
        warn_threshold=warn,
        crit_threshold=crit,
        tags={},
    )


def test_fingerprint_registered_for_each_breaching_metric():
    metrics = [
        _make_metric("orders", 50.0, 10.0, 40.0),
        _make_metric("invoices", 5.0, 10.0, 40.0),
    ]
    for m in metrics:
        results = evaluate_thresholds([m])
        for r in results:
            if r.level in ("warning", "critical"):
                register_fingerprint(r.pipeline, r.level, "value")

    fps = list_fingerprints()
    assert len(fps) == 1
    assert fps[0]["pipeline"] == "orders"
    assert fps[0]["level"] == "critical"


def test_repeated_breach_increments_hit_count():
    m = _make_metric("orders", 50.0, 10.0, 40.0)
    for _ in range(3):
        results = evaluate_thresholds([m])
        for r in results:
            if r.level in ("warning", "critical"):
                register_fingerprint(r.pipeline, r.level, "value")

    fps = list_fingerprints()
    assert fps[0]["hit_count"] == 3


def test_multiple_pipelines_have_independent_fingerprints():
    pipelines = ["alpha", "beta", "gamma"]
    for name in pipelines:
        m = _make_metric(name, 99.0, 10.0, 20.0)
        results = evaluate_thresholds([m])
        for r in results:
            if r.level in ("warning", "critical"):
                register_fingerprint(r.pipeline, r.level, "value")

    fps = list_fingerprints()
    names = {r["pipeline"] for r in fps}
    assert names == set(pipelines)
    for rec in fps:
        assert rec["hit_count"] == 1
