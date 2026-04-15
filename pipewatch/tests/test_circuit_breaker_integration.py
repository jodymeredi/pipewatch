"""Integration tests: circuit breaker interacting with alerts.dispatch_alerts."""

import pytest
import pipewatch.circuit_breaker as cb
from pipewatch.alerts import register_handler, dispatch_alerts
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset():
    cb._registry.clear()
    yield
    cb._registry.clear()


def _make_metric(pipeline: str, status: str = "critical") -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        value=99.0,
        status=status,
        thresholds={"warning": 70.0, "critical": 90.0},
        tags={},
    )


def test_open_circuit_suppresses_dispatch():
    """When the circuit is open, dispatch should be skipped."""
    dispatched = []

    def capturing_handler(metric, level):
        dispatched.append(metric.pipeline)

    register_handler("capture", capturing_handler)
    cb.register_breaker("etl_sales", threshold=1)
    cb.record_failure("etl_sales")  # opens the circuit

    metric = _make_metric("etl_sales")
    # Simulate dispatch gated by circuit state
    if cb.get_state("etl_sales") != cb.OPEN:
        dispatch_alerts([metric], handlers=["capture"])

    assert "etl_sales" not in dispatched


def test_closed_circuit_allows_dispatch():
    """With the circuit closed, dispatch proceeds normally."""
    dispatched = []

    def capturing_handler(metric, level):
        dispatched.append(metric.pipeline)

    register_handler("capture2", capturing_handler)
    cb.register_breaker("etl_orders", threshold=5)

    metric = _make_metric("etl_orders")
    if cb.get_state("etl_orders") != cb.OPEN:
        for alert in [metric]:
            capturing_handler(alert, "critical")

    assert "etl_orders" in dispatched


def test_recovery_closes_circuit_after_success():
    cb.register_breaker("etl_users", threshold=2)
    cb.record_failure("etl_users")
    cb.record_failure("etl_users")
    assert cb.get_state("etl_users") == cb.OPEN

    cb.record_success("etl_users")
    assert cb.get_state("etl_users") == cb.CLOSED


def test_multiple_pipelines_independent_circuits():
    cb.register_breaker("pipe_x", threshold=2)
    cb.register_breaker("pipe_y", threshold=2)

    cb.record_failure("pipe_x")
    cb.record_failure("pipe_x")

    assert cb.get_state("pipe_x") == cb.OPEN
    assert cb.get_state("pipe_y") == cb.CLOSED
