"""Integration tests for maintenance windows interacting with alert dispatch."""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

import pipewatch.maintenance as maint
import pipewatch.alerts as alerts
import pipewatch.metrics as metrics


@pytest.fixture(autouse=True)
def reset():
    maint._registry.clear()
    alerts._registry.clear()
    yield
    maint._registry.clear()
    alerts._registry.clear()


def _future(m: int = 30) -> datetime:
    return datetime.now(timezone.utc) + timedelta(minutes=m)


def _past(m: int = 30) -> datetime:
    return datetime.now(timezone.utc) - timedelta(minutes=m)


def _make_metric(name: str, status: str = "critical") -> metrics.PipelineMetric:
    return metrics.collect_metric(name, 99.0, status=status)


def test_pipeline_in_maintenance_skips_dispatch():
    dispatched: List[str] = []

    def capture(alert):
        dispatched.append(alert["pipeline"])

    alerts.register_handler("capture", capture)
    maint.add_window("pipe_a", _past(10), _future(10))

    m = _make_metric("pipe_a")
    if not maint.is_in_maintenance(m.pipeline):
        alerts.dispatch_alerts([m], ["capture"])

    assert "pipe_a" not in dispatched


def test_pipeline_not_in_maintenance_dispatches():
    dispatched: List[str] = []

    def capture(alert):
        dispatched.append(alert["pipeline"])

    alerts.register_handler("capture", capture)

    m = _make_metric("pipe_b")
    if not maint.is_in_maintenance(m.pipeline):
        alerts.dispatch_alerts([m], ["capture"])

    assert "pipe_b" in dispatched


def test_maintenance_window_expiry_allows_dispatch():
    dispatched: List[str] = []

    def capture(alert):
        dispatched.append(alert["pipeline"])

    alerts.register_handler("capture", capture)
    w = maint.add_window("pipe_c", _past(60), _past(5))

    m = _make_metric("pipe_c")
    if not maint.is_in_maintenance(m.pipeline):
        alerts.dispatch_alerts([m], ["capture"])

    assert "pipe_c" in dispatched


def test_multiple_pipelines_independent_maintenance():
    in_maint = []
    not_in_maint = []

    maint.add_window("pipe_x", _past(5), _future(5))

    for name in ["pipe_x", "pipe_y"]:
        if maint.is_in_maintenance(name):
            in_maint.append(name)
        else:
            not_in_maint.append(name)

    assert "pipe_x" in in_maint
    assert "pipe_y" in not_in_maint
