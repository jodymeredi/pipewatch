"""Integration tests: aggregation over live metrics collected via collect_metric."""

from pipewatch.aggregation import aggregate_bulk, aggregate_by_tag
from pipewatch.metrics import collect_metric, evaluate_thresholds


def _make_metric(pipeline, value, warn=50.0, crit=80.0):
    m = collect_metric(pipeline, value, tags=["integration"])
    thresholds = {"warning": warn, "critical": crit}
    evaluate_thresholds(m, thresholds)
    return m


def test_aggregate_reflects_evaluated_statuses():
    metrics = [
        _make_metric("pipe_a", 10.0),   # ok
        _make_metric("pipe_b", 60.0),   # warning
        _make_metric("pipe_c", 90.0),   # critical
    ]
    groups = {"all": metrics}
    results = aggregate_bulk(groups)
    assert len(results) == 1
    r = results[0]
    assert r.ok == 1
    assert r.warning == 1
    assert r.critical == 1


def test_aggregate_by_tag_only_includes_tagged():
    tagged = [_make_metric("t1", 5.0), _make_metric("t2", 5.0)]
    for m in tagged:
        m.tags = ["prod"]
    untagged = [_make_metric("u1", 5.0)]

    all_metrics = tagged + untagged
    result = aggregate_by_tag("prod", all_metrics)
    assert result.count == 2
    assert "u1" not in result.pipelines


def test_avg_value_matches_manual_calculation():
    values = [10.0, 20.0, 30.0]
    metrics = [_make_metric(f"p{i}", v) for i, v in enumerate(values)]
    from pipewatch.aggregation import aggregate_metrics
    result = aggregate_metrics("calc", metrics)
    assert result.avg_value == pytest.approx(20.0)


import pytest
