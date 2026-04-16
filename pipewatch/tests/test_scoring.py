"""Tests for pipewatch.scoring."""
import pytest
from pipewatch.scoring import (
    ScoreResult,
    as_dict,
    set_weight,
    score_pipeline,
    score_all,
    _LEVEL_WEIGHTS,
)
from pipewatch.metrics import PipelineMetric


def _make_metric(pipeline: str, name: str, value: float, status: str) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name=name, value=value, status=status)


# ---------------------------------------------------------------------------
# as_dict
# ---------------------------------------------------------------------------

def test_as_dict_serialisable():
    r = ScoreResult(pipeline="p", score=42.0, level="warning", contributors=["p:x=warning"])
    d = as_dict(r)
    assert d["pipeline"] == "p"
    assert d["score"] == 42.0
    assert d["level"] == "warning"
    assert d["contributors"] == ["p:x=warning"]


# ---------------------------------------------------------------------------
# set_weight
# ---------------------------------------------------------------------------

def test_set_weight_updates_level():
    original = _LEVEL_WEIGHTS["warning"]
    try:
        result = set_weight("warning", 0.6)
        assert result["warning"] == 0.6
    finally:
        _LEVEL_WEIGHTS["warning"] = original


def test_set_weight_invalid_level_raises():
    with pytest.raises(ValueError, match="Unknown level"):
        set_weight("unknown", 0.5)


def test_set_weight_out_of_range_raises():
    with pytest.raises(ValueError, match="between 0.0 and 1.0"):
        set_weight("critical", 1.5)


# ---------------------------------------------------------------------------
# score_pipeline
# ---------------------------------------------------------------------------

def test_score_pipeline_all_ok():
    metrics = [_make_metric("pipe", "rows", 100, "ok")]
    r = score_pipeline("pipe", metrics)
    assert r.score == 0.0
    assert r.level == "ok"
    assert r.contributors == []


def test_score_pipeline_all_critical():
    metrics = [_make_metric("pipe", "rows", 0, "critical")]
    r = score_pipeline("pipe", metrics)
    assert r.score == 100.0
    assert r.level == "critical"
    assert len(r.contributors) == 1


def test_score_pipeline_mixed():
    metrics = [
        _make_metric("pipe", "a", 1, "ok"),
        _make_metric("pipe", "b", 2, "warning"),
        _make_metric("pipe", "c", 3, "critical"),
    ]
    r = score_pipeline("pipe", metrics)
    assert 0 < r.score < 100
    assert r.level in ("warning", "critical")


def test_score_pipeline_no_metrics_returns_zero():
    r = score_pipeline("ghost", [])
    assert r.score == 0.0
    assert r.level == "ok"


def test_score_pipeline_filters_by_pipeline():
    metrics = [
        _make_metric("pipe_a", "x", 1, "critical"),
        _make_metric("pipe_b", "x", 1, "ok"),
    ]
    r = score_pipeline("pipe_b", metrics)
    assert r.score == 0.0


# ---------------------------------------------------------------------------
# score_all
# ---------------------------------------------------------------------------

def test_score_all_returns_one_result_per_pipeline():
    metrics = [
        _make_metric("alpha", "m", 1, "ok"),
        _make_metric("beta", "m", 1, "critical"),
    ]
    results = score_all(metrics)
    names = [r.pipeline for r in results]
    assert "alpha" in names
    assert "beta" in names
    assert len(results) == 2


def test_score_all_empty_list():
    assert score_all([]) == []
