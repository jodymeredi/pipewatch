"""Tests for pipewatch.grouping."""

from __future__ import annotations

import pytest

import pipewatch.grouping as grouping
from pipewatch.grouping import (
    create_group,
    remove_group,
    get_group,
    list_groups,
    add_pipeline_to_group,
    remove_pipeline_from_group,
    filter_metrics_by_group,
)
from pipewatch.metrics import collect_metric


@pytest.fixture(autouse=True)
def reset_registry():
    grouping._registry.clear()
    yield
    grouping._registry.clear()


def _make_metric(name: str, value: float = 1.0):
    return collect_metric(name, value)


# --- create_group ---

def test_create_group_returns_dict():
    result = create_group("prod", ["pipe_a", "pipe_b"])
    assert result["group"] == "prod"
    assert result["pipelines"] == ["pipe_a", "pipe_b"]


def test_create_group_deduplicates_pipelines():
    result = create_group("prod", ["pipe_a", "pipe_a", "pipe_b"])
    assert result["pipelines"] == ["pipe_a", "pipe_b"]


def test_create_group_blank_name_raises():
    with pytest.raises(ValueError, match="blank"):
        create_group("  ", ["pipe_a"])


def test_create_group_empty_pipelines_raises():
    with pytest.raises(ValueError, match="empty"):
        create_group("prod", [])


def test_create_group_blank_pipeline_entry_raises():
    with pytest.raises(ValueError, match="blank"):
        create_group("prod", ["pipe_a", ""])


def test_create_group_overwrites_existing():
    create_group("prod", ["pipe_a"])
    create_group("prod", ["pipe_b"])
    assert get_group("prod") == ["pipe_b"]


# --- remove_group ---

def test_remove_group_returns_true_when_present():
    create_group("staging", ["pipe_x"])
    assert remove_group("staging") is True


def test_remove_group_returns_false_when_absent():
    assert remove_group("nonexistent") is False


# --- get_group ---

def test_get_group_returns_copy():
    create_group("g", ["p1"])
    result = get_group("g")
    result.append("p2")
    assert get_group("g") == ["p1"]


def test_get_group_returns_none_for_missing():
    assert get_group("missing") is None


# --- list_groups ---

def test_list_groups_reflects_all_groups():
    create_group("a", ["p1"])
    create_group("b", ["p2", "p3"])
    result = list_groups()
    assert set(result.keys()) == {"a", "b"}


# --- add / remove pipeline ---

def test_add_pipeline_to_group_appends():
    create_group("g", ["p1"])
    result = add_pipeline_to_group("g", "p2")
    assert "p2" in result["pipelines"]


def test_add_pipeline_to_group_idempotent():
    create_group("g", ["p1"])
    add_pipeline_to_group("g", "p1")
    assert get_group("g") == ["p1"]


def test_add_pipeline_to_missing_group_raises():
    with pytest.raises(KeyError):
        add_pipeline_to_group("ghost", "p1")


def test_remove_pipeline_from_group_returns_true():
    create_group("g", ["p1", "p2"])
    assert remove_pipeline_from_group("g", "p1") is True
    assert get_group("g") == ["p2"]


def test_remove_pipeline_not_present_returns_false():
    create_group("g", ["p1"])
    assert remove_pipeline_from_group("g", "p99") is False


# --- filter_metrics_by_group ---

def test_filter_metrics_by_group_returns_matching():
    create_group("prod", ["alpha", "beta"])
    metrics = [_make_metric("alpha"), _make_metric("gamma")]
    result = filter_metrics_by_group("prod", metrics)
    assert len(result) == 1
    assert result[0].pipeline == "alpha"


def test_filter_metrics_by_group_unknown_group_returns_empty():
    metrics = [_make_metric("alpha")]
    assert filter_metrics_by_group("no_such_group", metrics) == []
