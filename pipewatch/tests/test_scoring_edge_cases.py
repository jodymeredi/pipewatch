"""Edge-case tests for pipewatch.scoring."""
import pytest
from pipewatch.metrics import PipelineMetric
from pipewatch.scoring import score_pipeline, score_all, as_dict, ScoreResult


def _m(pipeline, status):
    return PipelineMetric(pipeline=pipeline, name="x", value=1.0, status=status)


def test_score_100_is_critical():
    metrics = [_m("p", "critical")]
    r = score_pipeline("p", metrics)
    assert r.level == "critical"
    assert r.score == 100.0


def test_score_zero_is_ok():
    metrics = [_m("p", "ok")]
    r = score_pipeline("p", metrics)
    assert r.level == "ok"
    assert r.score == 0.0


def test_unknown_status_treated_as_zero_weight():
    metrics = [PipelineMetric(pipeline="p", name="x", value=1.0, status="unknown_level")]
    r = score_pipeline("p", metrics)
    assert r.score == 0.0


def test_contributors_only_include_non_ok():
    metrics = [
        _m("p", "ok"),
        _m("p", "warning"),
        _m("p", "critical"),
    ]
    r = score_pipeline("p", metrics)
    assert len(r.contributors) == 2


def test_score_all_preserves_pipeline_order():
    metrics = [
        _m("alpha", "ok"),
        _m("beta", "warning"),
        _m("gamma", "critical"),
    ]
    results = score_all(metrics)
    assert [r.pipeline for r in results] == ["alpha", "beta", "gamma"]


def test_as_dict_contributors_is_list():
    r = ScoreResult(pipeline="p", score=0.0, level="ok")
    d = as_dict(r)
    assert isinstance(d["contributors"], list)


def test_score_capped_at_100():
    """Even if weights were somehow inflated, score must not exceed 100."""
    from pipewatch.scoring import _LEVEL_WEIGHTS
    original = _LEVEL_WEIGHTS["critical"]
    try:
        _LEVEL_WEIGHTS["critical"] = 1.0  # normal max
        metrics = [_m("p", "critical")] * 10
        r = score_pipeline("p", metrics)
        assert r.score <= 100.0
    finally:
        _LEVEL_WEIGHTS["critical"] = original
