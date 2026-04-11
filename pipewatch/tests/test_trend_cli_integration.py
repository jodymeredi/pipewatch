"""Integration-level tests: trend analysis wired through CLI run()."""

import json
import sys
from unittest.mock import patch, MagicMock

import pytest

from pipewatch.trend import analyze_trend, TrendResult


# ---------------------------------------------------------------------------
# Helpers shared across tests
# ---------------------------------------------------------------------------

def _make_trend(direction: str) -> TrendResult:
    return TrendResult(
        pipeline="sales_etl",
        metric_name="row_count",
        direction=direction,
        first_value=100.0,
        last_value=120.0,
        sample_count=5,
        delta=20.0,
    )


# ---------------------------------------------------------------------------
# TrendResult dataclass
# ---------------------------------------------------------------------------

def test_trend_result_fields():
    t = _make_trend("stable")
    assert t.pipeline == "sales_etl"
    assert t.metric_name == "row_count"
    assert t.direction == "stable"
    assert t.sample_count == 5
    assert t.delta == 20.0


def test_trend_result_as_dict_serialisable():
    """TrendResult should be serialisable to JSON via __dict__."""
    t = _make_trend("degrading")
    payload = json.dumps(t.__dict__)
    recovered = json.loads(payload)
    assert recovered["direction"] == "degrading"
    assert recovered["first_value"] == 100.0


# ---------------------------------------------------------------------------
# analyze_trend with zero baseline (edge case)
# ---------------------------------------------------------------------------

def test_analyze_trend_zero_baseline(tmp_path):
    """When first value is 0, pct_change defaults to 0 → stable."""
    hist_dir = tmp_path / "history"
    hist_dir.mkdir()
    fpath = hist_dir / "pipe.jsonl"
    with fpath.open("w") as fh:
        for v in [0.0, 0.0, 0.0]:
            fh.write(json.dumps({"metrics": [{"pipeline": "p", "name": "m", "value": v}]}) + "\n")
    result = analyze_trend("p", "m", str(hist_dir))
    assert result.direction == "stable"
    assert result.delta == 0.0


# ---------------------------------------------------------------------------
# analyze_trend with missing metric entries (sparse data)
# ---------------------------------------------------------------------------

def test_analyze_trend_sparse_snapshots(tmp_path):
    """Snapshots that lack the target metric should be silently skipped."""
    hist_dir = tmp_path / "history"
    hist_dir.mkdir()
    fpath = hist_dir / "pipe.jsonl"
    snaps = [
        {"metrics": [{"pipeline": "p", "name": "row_count", "value": 10}]},
        {"metrics": [{"pipeline": "p", "name": "other_metric", "value": 999}]},
        {"metrics": [{"pipeline": "p", "name": "row_count", "value": 20}]},
        {"metrics": [{"pipeline": "p", "name": "row_count", "value": 30}]},
    ]
    with fpath.open("w") as fh:
        for s in snaps:
            fh.write(json.dumps(s) + "\n")
    result = analyze_trend("p", "row_count", str(hist_dir), min_samples=3)
    assert result.direction == "degrading"
    assert result.sample_count == 3


# ---------------------------------------------------------------------------
# summarize_trends edge case — empty list
# ---------------------------------------------------------------------------

def test_summarize_trends_empty_list():
    from pipewatch.trend import summarize_trends
    summary = summarize_trends([])
    assert all(v == 0 for v in summary.values())
