"""Unit tests for pipewatch.aggregation."""

import pytest

from pipewatch.aggregation import (
    AggregationResult,
    aggregate_bulk,
    aggregate_by_tag,
    aggregate_metrics,
    as_dict,
)
from pipewatch.metrics import PipelineMetric


def _m(pipeline: str, status: str = "ok", value: float = 0.0, tags=None) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, status=status, value=value, tags=tags or [])


def test_aggregate_metrics_counts_statuses():
    metrics = [_m("a", "ok"), _m("b", "warning"), _m("c", "critical")]
    result = aggregate_metrics("grp", metrics)
    assert result.ok == 1
    assert result.warning == 1
    assert result.critical == 1
    assert result.count == 3


def test_aggregate_metrics_computes_avg():
    metrics = [_m("a", value=10.0), _m("b", value=20.0)]
    result = aggregate_metrics("grp", metrics)
    assert result.avg_value == 15.0


def test_aggregate_metrics_computes_min_max():
    metrics = [_m("a", value=5.0), _m("b", value=15.0), _m("c", value=10.0)]
    result = aggregate_metrics("grp", metrics)
    assert result.min_value == 5.0
    assert result.max_value == 15.0


def test_aggregate_metrics_empty_list():
    result = aggregate_metrics("empty", [])
    assert result.count == 0
    assert result.avg_value is None
    assert result.min_value is None
    assert result.max_value is None


def test_aggregate_metrics_blank_group_raises():
    with pytest.raises(ValueError, match="blank"):
        aggregate_metrics("  ", [])


def test_aggregate_metrics_pipelines_list():
    metrics = [_m("pipe1"), _m("pipe2")]
    result = aggregate_metrics("g", metrics)
    assert set(result.pipelines) == {"pipe1", "pipe2"}


def test_as_dict_serialisable():
    result = aggregate_metrics("g", [_m("p", "ok", 1.0)])
    d = as_dict(result)
    import json
    json.dumps(d)  # must not raise


def test_aggregate_by_tag_filters_correctly():
    metrics = [
        _m("a", tags=["prod"]),
        _m("b", tags=["staging"]),
        _m("c", tags=["prod"]),
    ]
    result = aggregate_by_tag("prod", metrics)
    assert result.count == 2
    assert set(result.pipelines) == {"a", "c"}


def test_aggregate_by_tag_blank_raises():
    with pytest.raises(ValueError, match="blank"):
        aggregate_by_tag("", [])


def test_aggregate_bulk_returns_all_groups():
    groups = {
        "g1": [_m("p1", "ok")],
        "g2": [_m("p2", "critical")],
    }
    results = aggregate_bulk(groups)
    names = {r.group for r in results}
    assert names == {"g1", "g2"}
