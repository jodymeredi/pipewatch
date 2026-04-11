"""Tests for pipewatch/snapshot_diff.py."""

import pytest
from pipewatch.snapshot_diff import (
    DiffEntry,
    diff_snapshots,
    regressions,
    recoveries,
    _direction,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _m(pipeline: str, status: str, value: float = 1.0) -> dict:
    return {"pipeline": pipeline, "status": status, "value": value}


# ---------------------------------------------------------------------------
# _direction
# ---------------------------------------------------------------------------

def test_direction_stable():
    assert _direction("ok", "ok") == "stable"


def test_direction_regression():
    assert _direction("ok", "warning") == "regression"
    assert _direction("warning", "critical") == "regression"


def test_direction_recovery():
    assert _direction("critical", "ok") == "recovery"
    assert _direction("warning", "ok") == "recovery"


# ---------------------------------------------------------------------------
# diff_snapshots
# ---------------------------------------------------------------------------

def test_diff_returns_entry_for_each_pipeline():
    prev = [_m("pipe_a", "ok"), _m("pipe_b", "warning")]
    curr = [_m("pipe_a", "ok"), _m("pipe_b", "critical")]
    result = diff_snapshots(prev, curr)
    names = [e.pipeline for e in result]
    assert "pipe_a" in names
    assert "pipe_b" in names


def test_diff_stable_entry_not_changed():
    prev = [_m("pipe_a", "ok", 5.0)]
    curr = [_m("pipe_a", "ok", 6.0)]
    entry = diff_snapshots(prev, curr)[0]
    assert entry.changed is False
    assert entry.direction == "stable"


def test_diff_detects_regression():
    prev = [_m("pipe_a", "ok")]
    curr = [_m("pipe_a", "critical")]
    entry = diff_snapshots(prev, curr)[0]
    assert entry.changed is True
    assert entry.direction == "regression"


def test_diff_detects_recovery():
    prev = [_m("pipe_a", "critical")]
    curr = [_m("pipe_a", "ok")]
    entry = diff_snapshots(prev, curr)[0]
    assert entry.changed is True
    assert entry.direction == "recovery"


def test_diff_pipeline_only_in_previous():
    prev = [_m("pipe_gone", "ok")]
    curr: list = []
    entry = diff_snapshots(prev, curr)[0]
    assert entry.pipeline == "pipe_gone"
    assert entry.current_status == "unknown"


def test_diff_pipeline_only_in_current():
    prev: list = []
    curr = [_m("pipe_new", "warning")]
    entry = diff_snapshots(prev, curr)[0]
    assert entry.pipeline == "pipe_new"
    assert entry.previous_status == "unknown"


def test_diff_values_carried_through():
    prev = [_m("p", "ok", 3.5)]
    curr = [_m("p", "warning", 8.1)]
    entry = diff_snapshots(prev, curr)[0]
    assert entry.previous_value == pytest.approx(3.5)
    assert entry.current_value == pytest.approx(8.1)


# ---------------------------------------------------------------------------
# regressions / recoveries filters
# ---------------------------------------------------------------------------

def test_regressions_filter():
    prev = [_m("a", "ok"), _m("b", "critical"), _m("c", "warning")]
    curr = [_m("a", "warning"), _m("b", "ok"), _m("c", "warning")]
    entries = diff_snapshots(prev, curr)
    reg = regressions(entries)
    assert len(reg) == 1
    assert reg[0].pipeline == "a"


def test_recoveries_filter():
    prev = [_m("a", "ok"), _m("b", "critical")]
    curr = [_m("a", "critical"), _m("b", "ok")]
    entries = diff_snapshots(prev, curr)
    rec = recoveries(entries)
    assert len(rec) == 1
    assert rec[0].pipeline == "b"


# ---------------------------------------------------------------------------
# as_dict serialisation
# ---------------------------------------------------------------------------

def test_diff_entry_as_dict_keys():
    entry = DiffEntry(
        pipeline="p",
        previous_status="ok",
        current_status="warning",
        previous_value=1.0,
        current_value=2.0,
        changed=True,
        direction="regression",
    )
    d = entry.as_dict()
    expected_keys = {
        "pipeline", "previous_status", "current_status",
        "previous_value", "current_value", "changed", "direction",
    }
    assert set(d.keys()) == expected_keys
