"""Integration tests: correlation over real recorded history snapshots."""

from __future__ import annotations

import json
import math
import tempfile
from pathlib import Path

import pytest

from pipewatch.correlation import correlate_pipelines, find_correlated_pairs
from pipewatch.history import record_snapshot, load_snapshots
from pipewatch.metrics import PipelineMetric


@pytest.fixture()
def hist_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("PIPEWATCH_HISTORY_DIR", str(tmp_path))
    return tmp_path


def _metric(pipeline: str, value: float) -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        value=value,
        status="ok",
        tags={},
    )


def test_correlation_over_recorded_history(hist_dir):
    for v in [10.0, 20.0, 30.0, 40.0, 50.0]:
        record_snapshot([_metric("alpha", v), _metric("beta", v * 2)])

    snaps = load_snapshots()
    r = correlate_pipelines(snaps, "alpha", "beta")
    assert r is not None
    assert math.isclose(r.coefficient, 1.0, abs_tol=1e-9)
    assert r.strong is True
    assert r.sample_size == 5


def test_find_pairs_across_three_pipelines(hist_dir):
    values_a = [1, 2, 3, 4, 5, 6]
    values_b = [2, 4, 6, 8, 10, 12]  # perfect co-move with a
    values_c = [6, 5, 4, 3, 2, 1]   # perfect inverse of a

    for a, b, c in zip(values_a, values_b, values_c):
        record_snapshot([
            _metric("p_a", float(a)),
            _metric("p_b", float(b)),
            _metric("p_c", float(c)),
        ])

    snaps = load_snapshots()
    pairs = find_correlated_pairs(snaps, ["p_a", "p_b", "p_c"])
    assert len(pairs) == 3
    # Highest magnitude first — both (a,b) and (a,c) are coefficient=1.0 in magnitude
    magnitudes = [abs(p.coefficient) for p in pairs]
    assert magnitudes == sorted(magnitudes, reverse=True)


def test_correlation_with_single_snapshot_returns_none(hist_dir):
    record_snapshot([_metric("x", 1.0), _metric("y", 2.0)])
    snaps = load_snapshots()
    r = correlate_pipelines(snaps, "x", "y")
    assert r is None
