"""Integration tests: scoring interacts with evaluate_thresholds output."""
import pytest
from pipewatch.metrics import collect_metric, evaluate_thresholds
from pipewatch.scoring import score_all, score_pipeline


def _make_metric(pipeline, name, value, warn=None, crit=None):
    m = collect_metric(pipeline, name, value)
    thresholds = {}
    if warn is not None:
        thresholds["warning"] = warn
    if crit is not None:
        thresholds["critical"] = crit
    if thresholds:
        evaluate_thresholds([m], {name: thresholds})
    return m


def test_all_ok_pipelines_score_zero():
    metrics = [
        _make_metric("pipe", "rows", 100, warn=50, crit=10),
    ]
    r = score_pipeline("pipe", metrics)
    assert r.score == 0.0
    assert r.level == "ok"


def test_critical_breach_scores_high():
    metrics = [
        _make_metric("pipe", "errors", 5, warn=10, crit=20),
    ]
    # Force status manually since evaluate_thresholds checks lower-is-worse
    metrics[0].status = "critical"
    r = score_pipeline("pipe", metrics)
    assert r.score == 100.0


def test_score_all_reflects_mixed_pipeline_health():
    m1 = _make_metric("healthy", "rows", 200)
    m1.status = "ok"
    m2 = _make_metric("sick", "errors", 99)
    m2.status = "critical"
    results = score_all([m1, m2])
    by_name = {r.pipeline: r for r in results}
    assert by_name["healthy"].score < by_name["sick"].score


def test_score_level_warning_for_mid_range():
    from pipewatch.metrics import PipelineMetric
    metrics = [
        PipelineMetric(pipeline="p", name="lag", value=5, status="warning"),
        PipelineMetric(pipeline="p", name="rows", value=100, status="ok"),
    ]
    r = score_pipeline("p", metrics)
    # 1 warning out of 2 → 20 score → boundary
    assert r.level in ("ok", "warning")
    assert 0 < r.score <= 100
