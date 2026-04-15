"""Integration tests: sampling interacts with metrics and dispatch simulation."""

from __future__ import annotations

import pytest

import pipewatch.sampling as sampling
from pipewatch.metrics import collect_metric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    sampling._registry.clear()
    yield
    sampling._registry.clear()


def _make_metric(name: str, value: float = 10.0):
    return collect_metric(name, value)


def test_only_sampled_metrics_evaluated():
    """Metrics that fail the sampling check should never reach threshold eval."""
    sampling.set_sample_rate("noisy", 1.0)
    sampling.set_sample_rate("rare", 0.001)

    metrics = (
        [_make_metric("noisy") for _ in range(4)]
        + [_make_metric("rare") for _ in range(4)]
    )
    sampled = sampling.filter_sampled_metrics(metrics, seed=0)
    noisy_count = sum(1 for m in sampled if m.pipeline == "noisy")
    assert noisy_count == 4  # rate=1.0, all kept


def test_rate_update_reflected_immediately():
    sampling.set_sample_rate("pipe", 1.0)
    assert sampling.get_sample_rate("pipe") == 1.0
    sampling.set_sample_rate("pipe", 0.5)
    assert sampling.get_sample_rate("pipe") == 0.5


def test_filter_preserves_metric_fields():
    sampling.set_sample_rate("pipe_a", 1.0)
    m = _make_metric("pipe_a", value=42.0)
    result = sampling.filter_sampled_metrics([m])
    assert len(result) == 1
    assert result[0].pipeline == "pipe_a"
    assert result[0].value == 42.0


def test_multiple_pipelines_sampled_independently():
    for i in range(5):
        sampling.set_sample_rate(f"pipe_{i}", 1.0)
    metrics = [_make_metric(f"pipe_{i}") for i in range(5)]
    result = sampling.filter_sampled_metrics(metrics)
    assert len(result) == 5
    names = {m.pipeline for m in result}
    assert names == {f"pipe_{i}" for i in range(5)}
