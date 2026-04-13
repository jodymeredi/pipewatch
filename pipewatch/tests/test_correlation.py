"""Tests for pipewatch.correlation."""

from __future__ import annotations

import math
import pytest

from pipewatch.correlation import (
    CorrelationResult,
    as_dict,
    correlate_pipelines,
    find_correlated_pairs,
)


def _snapshot(values: dict) -> dict:
    """Build a minimal snapshot entry from {pipeline: value} mapping."""
    metrics = [
        {"pipeline": p, "value": v, "status": "ok", "tags": {}}
        for p, v in values.items()
    ]
    return {"recorded_at": "2024-01-01T00:00:00Z", "metrics": metrics}


def _snapshots_for(series: dict) -> list:
    """Build snapshot list from {pipeline: [values]} dict."""
    pipelines = list(series.keys())
    length = len(series[pipelines[0]])
    snaps = []
    for i in range(length):
        snaps.append(_snapshot({p: series[p][i] for p in pipelines}))
    return snaps


def test_correlate_perfectly_correlated():
    snaps = _snapshots_for({"a": [1, 2, 3, 4, 5], "b": [2, 4, 6, 8, 10]})
    r = correlate_pipelines(snaps, "a", "b")
    assert r is not None
    assert math.isclose(r.coefficient, 1.0, abs_tol=1e-9)
    assert r.strong is True
    assert r.sample_size == 5


def test_correlate_negatively_correlated():
    snaps = _snapshots_for({"a": [1, 2, 3, 4, 5], "b": [10, 8, 6, 4, 2]})
    r = correlate_pipelines(snaps, "a", "b")
    assert r is not None
    assert r.coefficient < -0.99
    assert r.strong is True


def test_correlate_insufficient_data():
    snaps = _snapshots_for({"a": [1], "b": [1]})
    r = correlate_pipelines(snaps, "a", "b")
    assert r is None


def test_correlate_constant_series_returns_none():
    snaps = _snapshots_for({"a": [3, 3, 3, 3], "b": [1, 2, 3, 4]})
    r = correlate_pipelines(snaps, "a", "b")
    assert r is None


def test_correlate_unknown_pipeline_returns_none():
    snaps = _snapshots_for({"a": [1, 2, 3]})
    r = correlate_pipelines(snaps, "a", "missing")
    assert r is None


def test_as_dict_serialisable():
    r = CorrelationResult("a", "b", 0.987654, 10, strong=True)
    d = as_dict(r)
    assert d["pipeline_a"] == "a"
    assert d["pipeline_b"] == "b"
    assert d["coefficient"] == 0.9877
    assert d["sample_size"] == 10
    assert d["strong"] is True


def test_find_correlated_pairs_returns_sorted_by_magnitude():
    snaps = _snapshots_for({
        "a": [1, 2, 3, 4, 5],
        "b": [2, 4, 6, 8, 10],  # perfect positive
        "c": [5, 3, 4, 2, 1],  # weak negative
    })
    pairs = find_correlated_pairs(snaps, ["a", "b", "c"])
    assert len(pairs) >= 1
    assert pairs[0].pipeline_a == "a"
    assert pairs[0].pipeline_b == "b"


def test_find_correlated_pairs_strong_threshold_filters():
    snaps = _snapshots_for({
        "a": [1, 2, 3, 4, 5],
        "b": [2, 4, 6, 8, 10],
        "c": [1, 3, 2, 4, 3],  # weak
    })
    pairs = find_correlated_pairs(snaps, ["a", "b", "c"], strong_threshold=0.75)
    strong_pairs = [p for p in pairs if p.strong]
    assert any(p.pipeline_a == "a" and p.pipeline_b == "b" for p in strong_pairs)
