"""Tests for pipewatch.dependency."""

import pytest

import pipewatch.dependency as dep


@pytest.fixture(autouse=True)
def reset_registry():
    dep.clear_dependencies()
    yield
    dep.clear_dependencies()


# ---------------------------------------------------------------------------
# add_dependency
# ---------------------------------------------------------------------------

def test_add_dependency_returns_dict():
    result = dep.add_dependency("transform", "ingest")
    assert result["pipeline"] == "transform"
    assert "ingest" in result["depends_on"]


def test_add_dependency_deduplicates():
    dep.add_dependency("transform", "ingest")
    result = dep.add_dependency("transform", "ingest")
    assert result["depends_on"].count("ingest") == 1


def test_add_dependency_multiple_upstreams():
    dep.add_dependency("load", "transform")
    result = dep.add_dependency("load", "validate")
    assert set(result["depends_on"]) == {"transform", "validate"}


def test_add_dependency_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline name"):
        dep.add_dependency("  ", "ingest")


def test_add_dependency_blank_upstream_raises():
    with pytest.raises(ValueError, match="depends_on"):
        dep.add_dependency("transform", "")


def test_add_dependency_self_raises():
    with pytest.raises(ValueError, match="cannot depend on itself"):
        dep.add_dependency("pipeline_a", "pipeline_a")


# ---------------------------------------------------------------------------
# remove_dependency
# ---------------------------------------------------------------------------

def test_remove_dependency_returns_true_when_present():
    dep.add_dependency("load", "transform")
    assert dep.remove_dependency("load", "transform") is True


def test_remove_dependency_returns_false_when_absent():
    assert dep.remove_dependency("load", "nonexistent") is False


def test_remove_dependency_cleans_up_empty_entry():
    dep.add_dependency("load", "transform")
    dep.remove_dependency("load", "transform")
    assert "load" not in dep.list_dependencies()


# ---------------------------------------------------------------------------
# get_dependencies / list_dependencies
# ---------------------------------------------------------------------------

def test_get_dependencies_returns_empty_list_for_unknown():
    assert dep.get_dependencies("unknown") == []


def test_list_dependencies_returns_all_entries():
    dep.add_dependency("a", "b")
    dep.add_dependency("c", "d")
    result = dep.list_dependencies()
    assert "a" in result and "c" in result


def test_list_dependencies_returns_copy():
    dep.add_dependency("a", "b")
    snapshot = dep.list_dependencies()
    snapshot["a"].append("injected")
    assert "injected" not in dep.get_dependencies("a")


# ---------------------------------------------------------------------------
# get_blocked_pipelines
# ---------------------------------------------------------------------------

def test_get_blocked_pipelines_returns_blocked():
    dep.add_dependency("load", "transform")
    dep.add_dependency("report", "load")
    blocked = dep.get_blocked_pipelines(["transform"])
    assert "load" in blocked
    assert "report" not in blocked  # direct dep 'load' is not in unhealthy list


def test_get_blocked_pipelines_empty_unhealthy_returns_empty():
    dep.add_dependency("load", "transform")
    assert dep.get_blocked_pipelines([]) == []


def test_get_blocked_pipelines_returns_sorted():
    dep.add_dependency("zebra", "src")
    dep.add_dependency("alpha", "src")
    blocked = dep.get_blocked_pipelines(["src"])
    assert blocked == sorted(blocked)
