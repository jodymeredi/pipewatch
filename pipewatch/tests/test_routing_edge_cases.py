"""Edge-case tests for pipewatch.routing."""

import pytest

import pipewatch.routing as routing


@pytest.fixture(autouse=True)
def reset_registry():
    routing.clear_routes()
    yield
    routing.clear_routes()


def test_resolve_returns_empty_list_when_no_route_and_no_defaults():
    assert routing.resolve_channels("orphan_pipe") == []


def test_list_routes_returns_copies_not_references():
    routing.set_route("pipe_a", ["slack"])
    rules = routing.list_routes()
    rules[0]["channels"].append("injected")
    # internal state should be unaffected
    assert routing.get_route("pipe_a") == ["slack"]


def test_get_route_returns_copy_not_reference():
    routing.set_route("pipe_a", ["slack"])
    ch = routing.get_route("pipe_a")
    ch.append("injected")
    assert routing.get_route("pipe_a") == ["slack"]


def test_set_route_whitespace_only_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline name"):
        routing.set_route("   ", ["slack"])


def test_overwrite_default_channels():
    routing.set_default_channels(["email"])
    routing.set_default_channels(["slack", "webhook"])
    assert routing.resolve_channels("anything") == ["slack", "webhook"]


def test_many_pipelines_independent():
    for i in range(10):
        routing.set_route(f"pipe_{i}", [f"channel_{i}"])
    for i in range(10):
        assert routing.resolve_channels(f"pipe_{i}") == [f"channel_{i}"]


def test_remove_then_re_add_route():
    routing.set_route("etl", ["slack"])
    routing.remove_route("etl")
    routing.set_route("etl", ["email"])
    assert routing.get_route("etl") == ["email"]


def test_list_routes_after_clear_is_empty():
    routing.set_route("pipe_a", ["slack"])
    routing.clear_routes()
    assert routing.list_routes() == []
