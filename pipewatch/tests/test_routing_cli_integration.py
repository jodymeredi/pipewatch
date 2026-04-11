"""CLI-style integration tests: simulate routing sub-command workflows."""

import pytest

import pipewatch.routing as routing


@pytest.fixture(autouse=True)
def reset():
    routing.clear_routes()
    yield
    routing.clear_routes()


def _simulate_set(pipeline: str, channels):
    """Simulate: pipewatch routing set <pipeline> <channels...>"""
    return routing.set_route(pipeline, channels)


def _simulate_get(pipeline: str):
    """Simulate: pipewatch routing get <pipeline>"""
    return routing.resolve_channels(pipeline)


def _simulate_list():
    """Simulate: pipewatch routing list"""
    return routing.list_routes()


def _simulate_remove(pipeline: str):
    """Simulate: pipewatch routing remove <pipeline>"""
    return routing.remove_route(pipeline)


def test_set_returns_correct_dict():
    result = _simulate_set("etl_sales", ["slack", "email"])
    assert result["pipeline"] == "etl_sales"
    assert result["channels"] == ["slack", "email"]


def test_get_after_set_returns_channels():
    _simulate_set("etl_sales", ["slack"])
    assert _simulate_get("etl_sales") == ["slack"]


def test_list_shows_all_pipelines():
    _simulate_set("pipe_a", ["slack"])
    _simulate_set("pipe_b", ["email"])
    rules = _simulate_list()
    names = {r["pipeline"] for r in rules}
    assert names == {"pipe_a", "pipe_b"}


def test_remove_then_list_excludes_pipeline():
    _simulate_set("pipe_a", ["slack"])
    _simulate_set("pipe_b", ["email"])
    _simulate_remove("pipe_a")
    names = {r["pipeline"] for r in _simulate_list()}
    assert "pipe_a" not in names
    assert "pipe_b" in names


def test_full_workflow_set_get_remove_fallback():
    routing.set_default_channels(["log"])
    _simulate_set("etl_orders", ["pagerduty"])
    assert _simulate_get("etl_orders") == ["pagerduty"]
    _simulate_remove("etl_orders")
    # should fall back to default
    assert _simulate_get("etl_orders") == ["log"]
