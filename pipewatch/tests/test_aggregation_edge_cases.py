"""Edge-case tests for pipewatch.aggregation."""

import pytest

from pipewatch.aggregation import aggregate_metrics, aggregate_by_tag, as_dict
from pipewatch.metrics import PipelineMetric


def _m(pipeline, status="ok", value=0.0, tags=None):
    return PipelineMetric(pipeline=pipeline, status=status, value=value, tags=tags or [])


def test_none_value_excluded_from_stats():
    m1 = PipelineMetric(pipeline="a", status="ok", value=None, tags=[])
    m2 = _m("b", value=10.0)
    result = aggregate_metrics("g", [m1, m2])
    assert result.avg_value == 10.0
    assert result.min_value == 10.0
    assert result.max_value == 10.0


def test_all_none_values_yields_none_stats():
    metrics = [
        PipelineMetric(pipeline="a", status="ok", value=None, tags=[]),
        PipelineMetric(pipeline="b", status="ok", value=None, tags=[]),
    ]
    result = aggregate_metrics("g", metrics)
    assert result.avg_value is None
    assert result.min_value is None
    assert result.max_value is None


def test_group_name_stripped():
    result = aggregate_metrics("  grp  ", [])
    assert result.group == "grp"


def test_single_metric_avg_equals_value():
    result = aggregate_metrics("g", [_m("only", value=42.0)])
    assert result.avg_value == 42.0


def test_aggregate_by_tag_no_matches_returns_empty():
    metrics = [_m("a", tags=["staging"])]
    result = aggregate_by_tag("prod", metrics)
    assert result.count == 0
    assert result.pipelines == []


def test_as_dict_has_expected_keys():
    result = aggregate_metrics("g", [])
    d = as_dict(result)
    for key in ("group", "pipelines", "count", "ok", "warning", "critical",
                "avg_value", "max_value", "min_value"):
        assert key in d
