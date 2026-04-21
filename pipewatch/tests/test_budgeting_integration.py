"""Integration tests: budgeting interacts with metrics + dispatch simulation."""

from __future__ import annotations

import pytest

from pipewatch.budgeting import (
    is_over_budget,
    record_alert,
    remaining,
    reset_all,
    set_budget,
)
from pipewatch.metrics import PipelineMetric, collect_metric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    reset_all()
    yield
    reset_all()


def _make_metric(pipeline: str, value: float, warn: float = 80.0, crit: float = 90.0) -> PipelineMetric:
    m = collect_metric(pipeline, value)
    thresholds = {"warning": warn, "critical": crit}
    return evaluate_thresholds(m, thresholds)


def _simulate_dispatch(metrics, fired: list) -> None:
    """Fake dispatch: fires an alert if not over budget, records it."""
    for m in metrics:
        if m.status == "ok":
            continue
        if is_over_budget(m.pipeline):
            continue
        fired.append(m.pipeline)
        record_alert(m.pipeline)


# ---------------------------------------------------------------------------
# tests
# ---------------------------------------------------------------------------


def test_dispatch_respects_budget():
    set_budget("pipe_a", max_alerts=2, window_seconds=3600)

    metrics = [_make_metric("pipe_a", 95.0)] * 5
    fired: list = []
    _simulate_dispatch(metrics, fired)

    assert fired.count("pipe_a") == 2


def test_dispatch_allowed_when_budget_not_exhausted():
    set_budget("pipe_a", max_alerts=10, window_seconds=3600)

    metrics = [_make_metric("pipe_a", 95.0)] * 3
    fired: list = []
    _simulate_dispatch(metrics, fired)

    assert fired.count("pipe_a") == 3
    assert remaining("pipe_a") == 7


def test_ok_metrics_not_counted_against_budget():
    set_budget("pipe_a", max_alerts=1, window_seconds=3600)

    ok_metrics = [_make_metric("pipe_a", 50.0)] * 5
    fired: list = []
    _simulate_dispatch(ok_metrics, fired)

    assert fired == []
    assert remaining("pipe_a") == 1


def test_multiple_pipelines_have_independent_budgets():
    set_budget("pipe_a", max_alerts=1, window_seconds=3600)
    set_budget("pipe_b", max_alerts=3, window_seconds=3600)

    metrics = [
        _make_metric("pipe_a", 95.0),
        _make_metric("pipe_a", 95.0),
        _make_metric("pipe_b", 95.0),
        _make_metric("pipe_b", 95.0),
    ]
    fired: list = []
    _simulate_dispatch(metrics, fired)

    assert fired.count("pipe_a") == 1
    assert fired.count("pipe_b") == 2
