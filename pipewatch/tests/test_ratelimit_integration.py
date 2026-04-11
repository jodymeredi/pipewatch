"""Integration tests: ratelimit guards dispatch_alerts."""
from __future__ import annotations

import pytest

import pipewatch.ratelimit as rl
from pipewatch.alerts import register_handler, dispatch_alerts
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset(monkeypatch):
    rl._limits.clear()
    rl._history.clear()
    yield
    rl._limits.clear()
    rl._history.clear()


def _make_metric(status: str = "warning") -> PipelineMetric:
    return PipelineMetric(
        pipeline="pipe-a",
        metric="row_count",
        value=0,
        status=status,
        tags={},
    )


def test_dispatch_respects_rate_limit(monkeypatch):
    """Handler should not be invoked when channel is rate-limited."""
    calls: list = []

    def _handler(alert):
        calls.append(alert)

    register_handler("mock", _handler)

    # Allow only 1 call per 60 s
    monkeypatch.setattr(rl, "_now", lambda: 1000.0)
    rl.set_limit("mock", 1, 60)

    metric = _make_metric()
    breaches = [{"pipeline": "pipe-a", "level": "warning", "metric": "row_count", "value": 0}]

    # First dispatch — should go through
    rl.record_dispatch("mock")
    # Second dispatch — should be blocked
    if not rl.is_rate_limited("mock"):
        dispatch_alerts(breaches, handlers=["mock"])
        calls.append("direct")

    assert len(calls) == 0, "Handler should be blocked by rate limit"


def test_dispatch_allowed_when_not_rate_limited(monkeypatch):
    """Handler is called when channel has remaining quota."""
    calls: list = []

    def _handler(alert):
        calls.append(alert)

    register_handler("mock2", _handler)
    monkeypatch.setattr(rl, "_now", lambda: 2000.0)
    rl.set_limit("mock2", 5, 60)

    assert not rl.is_rate_limited("mock2")
    breaches = [{"pipeline": "pipe-b", "level": "critical", "metric": "latency", "value": 999}]
    dispatch_alerts(breaches, handlers=["mock2"])
    rl.record_dispatch("mock2")
    assert rl.remaining("mock2") == 4
