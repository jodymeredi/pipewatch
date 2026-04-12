"""Integration tests: tagging interacts with metrics filtering and dispatch."""

import pytest

from pipewatch.tagging import (
    tag_pipeline,
    filter_metrics_by_tag,
    pipelines_for_tag,
    clear_registry,
)
from pipewatch.metrics import PipelineMetric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    clear_registry()
    yield
    clear_registry()


def _make_metric(pipeline: str, value: float, status: str = "ok") -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, value=value, status=status, level="info")


def test_filter_only_prod_metrics():
    tag_pipeline("orders_etl", ["env:prod"])
    tag_pipeline("users_etl", ["env:prod"])
    tag_pipeline("dev_pipeline", ["env:dev"])

    metrics = [
        _make_metric("orders_etl", 10.0),
        _make_metric("users_etl", 20.0),
        _make_metric("dev_pipeline", 5.0),
    ]

    prod_metrics = filter_metrics_by_tag(metrics, "env:prod")
    pipelines = [m.pipeline for m in prod_metrics]
    assert "orders_etl" in pipelines
    assert "users_etl" in pipelines
    assert "dev_pipeline" not in pipelines


def test_tag_then_untag_no_longer_in_filter():
    from pipewatch.tagging import untag_pipeline

    tag_pipeline("orders_etl", ["env:prod"])
    untag_pipeline("orders_etl", ["env:prod"])

    metrics = [_make_metric("orders_etl", 10.0)]
    result = filter_metrics_by_tag(metrics, "env:prod")
    assert result == []


def test_multiple_tags_pipeline_appears_in_multiple_groups():
    tag_pipeline("shared_etl", ["env:prod", "team:platform"])

    assert "shared_etl" in pipelines_for_tag("env:prod")
    assert "shared_etl" in pipelines_for_tag("team:platform")


def test_filter_metrics_empty_list_returns_empty():
    tag_pipeline("orders_etl", ["env:prod"])
    result = filter_metrics_by_tag([], "env:prod")
    assert result == []


def test_untagged_pipeline_metrics_not_included():
    # no tag_pipeline call for "orphan"
    metrics = [_make_metric("orphan", 99.0)]
    result = filter_metrics_by_tag(metrics, "env:prod")
    assert result == []
