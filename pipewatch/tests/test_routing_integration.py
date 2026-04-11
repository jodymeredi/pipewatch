"""Integration tests: routing interacts with alerts.dispatch_alerts."""

import pytest

import pipewatch.routing as routing
import pipewatch.alerts as alerts
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset():
    routing.clear_routes()
    # clear alert handlers between tests
    alerts._handlers.clear()  # type: ignore[attr-defined]
    yield
    routing.clear_routes()
    alerts._handlers.clear()  # type: ignore[attr-defined]


def _make_metric(name: str, status: str = "warning") -> PipelineMetric:
    return PipelineMetric(
        pipeline=name,
        metric_name="row_count",
        value=10.0,
        status=status,
        tags={},
    )


def test_routed_channels_receive_dispatch():
    received: list = []

    def capture_handler(metric, cfg):
        received.append((metric.pipeline, cfg.get("channel")))

    alerts.register_handler("slack", capture_handler)
    alerts.register_handler("email", capture_handler)

    routing.set_route("etl_sales", ["slack"])
    channels = routing.resolve_channels("etl_sales")

    metric = _make_metric("etl_sales")
    for ch in channels:
        handler = alerts.get_handler(ch)
        if handler:
            handler(metric, {"channel": ch})

    assert len(received) == 1
    assert received[0] == ("etl_sales", "slack")


def test_default_channel_used_when_no_explicit_route():
    received: list = []

    def capture_handler(metric, cfg):
        received.append(cfg.get("channel"))

    alerts.register_handler("webhook", capture_handler)
    routing.set_default_channels(["webhook"])

    channels = routing.resolve_channels("unknown_pipe")
    metric = _make_metric("unknown_pipe")
    for ch in channels:
        handler = alerts.get_handler(ch)
        if handler:
            handler(metric, {"channel": ch})

    assert received == ["webhook"]


def test_multiple_channels_all_called():
    received: list = []

    def capture(metric, cfg):
        received.append(cfg.get("channel"))

    alerts.register_handler("slack", capture)
    alerts.register_handler("email", capture)

    routing.set_route("etl_orders", ["slack", "email"])
    channels = routing.resolve_channels("etl_orders")
    metric = _make_metric("etl_orders")
    for ch in channels:
        handler = alerts.get_handler(ch)
        if handler:
            handler(metric, {"channel": ch})

    assert sorted(received) == ["email", "slack"]
