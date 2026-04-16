"""Simulate CLI-level usage of aggregation (no actual CLI wiring yet)."""

import json
import pytest

from pipewatch.aggregation import aggregate_bulk, aggregate_metrics, as_dict
from pipewatch.metrics import PipelineMetric


def _m(pipeline, status="ok", value=0.0, tags=None):
    return PipelineMetric(pipeline=pipeline, status=status, value=value, tags=tags or [])


def _simulate_aggregate(group, metrics):
    result = aggregate_metrics(group, metrics)
    return as_dict(result)


def _simulate_bulk(groups):
    results = aggregate_bulk(groups)
    return [as_dict(r) for r in results]


def test_simulate_aggregate_returns_serialisable_dict():
    metrics = [_m("p1", "ok", 5.0), _m("p2", "critical", 95.0)]
    d = _simulate_aggregate("mygroup", metrics)
    json.dumps(d)  # must not raise
    assert d["group"] == "mygroup"
    assert d["count"] == 2


def test_simulate_bulk_multiple_groups():
    groups = {
        "prod": [_m("p1", "ok"), _m("p2", "warning")],
        "staging": [_m("s1", "critical")],
    }
    results = _simulate_bulk(groups)
    assert len(results) == 2
    group_names = {r["group"] for r in results}
    assert group_names == {"prod", "staging"}


def test_simulate_aggregate_ok_count_correct():
    metrics = [_m("a", "ok"), _m("b", "ok"), _m("c", "warning")]
    d = _simulate_aggregate("g", metrics)
    assert d["ok"] == 2
    assert d["warning"] == 1
    assert d["critical"] == 0


def test_simulate_aggregate_empty_group_serialisable():
    d = _simulate_aggregate("empty", [])
    json.dumps(d)
    assert d["count"] == 0
    assert d["avg_value"] is None
