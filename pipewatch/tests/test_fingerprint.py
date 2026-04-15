"""Tests for pipewatch.fingerprint."""

from __future__ import annotations

import pytest

import pipewatch.fingerprint as fp_mod
from pipewatch.fingerprint import (
    register_fingerprint,
    get_fingerprint,
    remove_fingerprint,
    list_fingerprints,
    reset_registry,
)


@pytest.fixture(autouse=True)
def reset_registry():
    fp_mod.reset_registry()
    yield
    fp_mod.reset_registry()


def test_register_fingerprint_returns_dict():
    rec = register_fingerprint("orders", "critical", "row_count")
    assert isinstance(rec, dict)
    assert rec["pipeline"] == "orders"
    assert rec["level"] == "critical"
    assert rec["metric_name"] == "row_count"
    assert len(rec["fingerprint"]) == 16


def test_register_fingerprint_hit_count_increments():
    register_fingerprint("orders", "critical", "row_count")
    rec2 = register_fingerprint("orders", "critical", "row_count")
    assert rec2["hit_count"] == 2


def test_register_fingerprint_different_triple_different_fp():
    r1 = register_fingerprint("orders", "critical", "row_count")
    r2 = register_fingerprint("orders", "warning", "row_count")
    assert r1["fingerprint"] != r2["fingerprint"]


def test_register_fingerprint_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline"):
        register_fingerprint("  ", "critical", "row_count")


def test_register_fingerprint_blank_level_raises():
    with pytest.raises(ValueError, match="level"):
        register_fingerprint("orders", "", "row_count")


def test_register_fingerprint_blank_metric_raises():
    with pytest.raises(ValueError, match="metric_name"):
        register_fingerprint("orders", "critical", "")


def test_get_fingerprint_returns_none_when_missing():
    assert get_fingerprint("unknown", "critical", "row_count") is None


def test_get_fingerprint_returns_record_after_register():
    register_fingerprint("invoices", "warning", "latency")
    rec = get_fingerprint("invoices", "warning", "latency")
    assert rec is not None
    assert rec["pipeline"] == "invoices"


def test_get_fingerprint_returns_copy_not_reference():
    register_fingerprint("invoices", "warning", "latency")
    rec = get_fingerprint("invoices", "warning", "latency")
    rec["hit_count"] = 9999
    rec2 = get_fingerprint("invoices", "warning", "latency")
    assert rec2["hit_count"] == 1


def test_remove_fingerprint_returns_true_when_present():
    register_fingerprint("orders", "critical", "row_count")
    assert remove_fingerprint("orders", "critical", "row_count") is True


def test_remove_fingerprint_returns_false_when_absent():
    assert remove_fingerprint("orders", "critical", "row_count") is False


def test_remove_fingerprint_clears_record():
    register_fingerprint("orders", "critical", "row_count")
    remove_fingerprint("orders", "critical", "row_count")
    assert get_fingerprint("orders", "critical", "row_count") is None


def test_list_fingerprints_returns_all():
    register_fingerprint("orders", "critical", "row_count")
    register_fingerprint("invoices", "warning", "latency")
    fps = list_fingerprints()
    pipelines = {r["pipeline"] for r in fps}
    assert pipelines == {"orders", "invoices"}


def test_fingerprint_level_case_normalised():
    r1 = register_fingerprint("orders", "CRITICAL", "row_count")
    r2 = register_fingerprint("orders", "critical", "row_count")
    assert r1["fingerprint"] == r2["fingerprint"]
    assert r2["hit_count"] == 2
