"""Tests for pipewatch.tagging."""

import pytest

import pipewatch.tagging as tagging
from pipewatch.tagging import (
    tag_pipeline,
    untag_pipeline,
    get_tags,
    pipelines_for_tag,
    filter_metrics_by_tag,
    list_tags,
    clear_registry,
)
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset_registry():
    clear_registry()
    yield
    clear_registry()


def _make_metric(pipeline: str) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, value=1.0, status="ok", level="info")


# --- tag_pipeline ---

def test_tag_pipeline_returns_dict_with_tags():
    result = tag_pipeline("etl_orders", ["team:data", "env:prod"])
    assert result["pipeline"] == "etl_orders"
    assert "team:data" in result["tags"]
    assert "env:prod" in result["tags"]


def test_tag_pipeline_empty_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline name"):
        tag_pipeline("", ["env:prod"])


def test_tag_pipeline_empty_tags_raises():
    with pytest.raises(ValueError, match="tags list"):
        tag_pipeline("etl_orders", [])


def test_tag_pipeline_blank_tag_entry_raises():
    with pytest.raises(ValueError, match="non-empty"):
        tag_pipeline("etl_orders", ["valid", "  "])


def test_tag_pipeline_accumulates_tags():
    tag_pipeline("etl_orders", ["env:prod"])
    tag_pipeline("etl_orders", ["team:data"])
    assert set(get_tags("etl_orders")) == {"env:prod", "team:data"}


# --- untag_pipeline ---

def test_untag_pipeline_removes_tag():
    tag_pipeline("etl_orders", ["env:prod", "team:data"])
    removed = untag_pipeline("etl_orders", ["env:prod"])
    assert removed is True
    assert "env:prod" not in get_tags("etl_orders")


def test_untag_pipeline_unknown_pipeline_returns_false():
    assert untag_pipeline("ghost", ["env:prod"]) is False


def test_untag_pipeline_removes_from_tag_index():
    tag_pipeline("etl_orders", ["env:prod"])
    untag_pipeline("etl_orders", ["env:prod"])
    assert "etl_orders" not in pipelines_for_tag("env:prod")


# --- get_tags / pipelines_for_tag ---

def test_get_tags_returns_empty_for_unknown():
    assert get_tags("unknown") == []


def test_pipelines_for_tag_returns_all_tagged_pipelines():
    tag_pipeline("etl_orders", ["env:prod"])
    tag_pipeline("etl_users", ["env:prod"])
    result = pipelines_for_tag("env:prod")
    assert "etl_orders" in result
    assert "etl_users" in result


# --- filter_metrics_by_tag ---

def test_filter_metrics_by_tag_returns_matching():
    tag_pipeline("etl_orders", ["env:prod"])
    metrics = [_make_metric("etl_orders"), _make_metric("etl_users")]
    result = filter_metrics_by_tag(metrics, "env:prod")
    assert len(result) == 1
    assert result[0].pipeline == "etl_orders"


def test_filter_metrics_by_tag_returns_empty_when_no_match():
    metrics = [_make_metric("etl_orders")]
    result = filter_metrics_by_tag(metrics, "env:staging")
    assert result == []


# --- list_tags ---

def test_list_tags_returns_all_tags():
    tag_pipeline("etl_orders", ["env:prod", "team:data"])
    tags = list_tags()
    assert "env:prod" in tags
    assert "team:data" in tags


def test_list_tags_empty_after_clear():
    tag_pipeline("etl_orders", ["env:prod"])
    clear_registry()
    assert list_tags() == {}
