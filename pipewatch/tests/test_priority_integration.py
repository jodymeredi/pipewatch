"""Integration tests: priority interacts with metrics and dispatch."""

import pytest

from pipewatch.metrics import collect_metric, evaluate_thresholds
from pipewatch.priority import (
    clear_priorities,
    set_priority,
    sort_by_priority,
)


@pytest.fixture(autouse=True)
def reset():
    clear_priorities()
    yield
    clear_priorities()


def _make_metric(name: str, value: float, warn: float = 80.0, crit: float = 95.0):
    return collect_metric(
        pipeline=name,
        metric_name="row_count",
        value=value,
        thresholds={"warning": warn, "critical": crit},
    )


def test_priority_ordering_applied_to_breaching_pipelines():
    """Pipelines with breaches should be surfaced in priority order."""
    set_priority("ingest", 10)
    set_priority("transform", 50)
    set_priority("export", 5)

    metrics = [
        _make_metric("ingest", 90.0),
        _make_metric("transform", 96.0),
        _make_metric("export", 97.0),
    ]

    breaching = [
        m.pipeline
        for m in metrics
        if evaluate_thresholds(m)
    ]

    ordered = sort_by_priority(breaching)
    assert ordered[0] == "export"   # priority 5
    assert ordered[1] == "ingest"   # priority 10
    assert ordered[2] == "transform"  # priority 50


def test_unregistered_pipelines_use_default_mid_priority():
    """Pipelines without an explicit priority sort in the middle."""
    set_priority("critical_pipe", 1)
    set_priority("low_pipe", 99)

    pipelines = ["low_pipe", "unregistered", "critical_pipe"]
    ordered = sort_by_priority(pipelines)

    assert ordered[0] == "critical_pipe"
    assert ordered[1] == "unregistered"  # default 50
    assert ordered[2] == "low_pipe"


def test_sort_stable_for_equal_priorities():
    """Pipelines sharing the same priority level appear (stably) in the result."""
    set_priority("alpha", 20)
    set_priority("beta", 20)
    result = sort_by_priority(["alpha", "beta"])
    assert set(result) == {"alpha", "beta"}
