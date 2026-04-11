"""Unit tests for pipewatch.routing."""

import pytest

import pipewatch.routing as routing


@pytest.fixture(autouse=True)
def reset_registry():
    routing.clear_routes()
    yield
    routing.clear_routes()


# ---------------------------------------------------------------------------
# set_route
# ---------------------------------------------------------------------------

def test_set_route_returns_dict():
    result = routing.set_route("etl_sales", ["slack", "email"])
    assert result == {"pipeline": "etl_sales", "channels": ["slack", "email"]}


def test_set_route_empty_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline name"):
        routing.set_route("", ["slack"])


def test_set_route_empty_channels_raises():
    with pytest.raises(ValueError, match="channels list must not be empty"):
        routing.set_route("etl_sales", [])


def test_set_route_blank_channel_entries_raises():
    with pytest.raises(ValueError, match="no valid entries"):
        routing.set_route("etl_sales", ["", "  "])


def test_set_route_overwrites_existing():
    routing.set_route("etl_sales", ["slack"])
    routing.set_route("etl_sales", ["email"])
    assert routing.get_route("etl_sales") == ["email"]


# ---------------------------------------------------------------------------
# get_route / resolve_channels
# ---------------------------------------------------------------------------

def test_get_route_returns_assigned_channels():
    routing.set_route("etl_sales", ["pagerduty"])
    assert routing.get_route("etl_sales") == ["pagerduty"]


def test_get_route_returns_defaults_when_no_match():
    routing.set_default_channels(["webhook"])
    assert routing.get_route("unknown_pipeline") == ["webhook"]


def test_resolve_channels_uses_explicit_over_default():
    routing.set_default_channels(["webhook"])
    routing.set_route("etl_sales", ["slack"])
    assert routing.resolve_channels("etl_sales") == ["slack"]


# ---------------------------------------------------------------------------
# remove_route
# ---------------------------------------------------------------------------

def test_remove_route_returns_true_when_present():
    routing.set_route("etl_sales", ["slack"])
    assert routing.remove_route("etl_sales") is True


def test_remove_route_returns_false_when_absent():
    assert routing.remove_route("nonexistent") is False


def test_remove_route_falls_back_to_defaults_afterwards():
    routing.set_default_channels(["email"])
    routing.set_route("etl_sales", ["slack"])
    routing.remove_route("etl_sales")
    assert routing.resolve_channels("etl_sales") == ["email"]


# ---------------------------------------------------------------------------
# list_routes
# ---------------------------------------------------------------------------

def test_list_routes_empty_initially():
    assert routing.list_routes() == []


def test_list_routes_reflects_added_rules():
    routing.set_route("pipe_a", ["slack"])
    routing.set_route("pipe_b", ["email", "webhook"])
    rules = routing.list_routes()
    pipelines = {r["pipeline"] for r in rules}
    assert pipelines == {"pipe_a", "pipe_b"}


# ---------------------------------------------------------------------------
# set_default_channels
# ---------------------------------------------------------------------------

def test_set_default_channels_empty_raises():
    with pytest.raises(ValueError, match="default channels"):
        routing.set_default_channels([])


def test_set_default_channels_unknown_pipeline_uses_defaults():
    routing.set_default_channels(["log", "email"])
    assert routing.resolve_channels("any_pipeline") == ["log", "email"]
