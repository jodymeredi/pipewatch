"""Tests for pipewatch.quota."""

from __future__ import annotations

import pytest

import pipewatch.quota as quota_mod
from pipewatch.quota import (
    clear_counts,
    get_quota,
    is_quota_exceeded,
    list_quotas,
    record_alert,
    remaining,
    remove_quota,
    set_quota,
)


@pytest.fixture(autouse=True)
def reset_registry():
    quota_mod._registry.clear()
    quota_mod._counts.clear()
    yield
    quota_mod._registry.clear()
    quota_mod._counts.clear()


def test_set_quota_returns_dict():
    rule = set_quota("etl_load", max_alerts=5, window_seconds=600)
    assert rule == {"pipeline": "etl_load", "max_alerts": 5, "window_seconds": 600}


def test_set_quota_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        set_quota("  ", max_alerts=3)


def test_set_quota_zero_max_alerts_raises():
    with pytest.raises(ValueError, match="max_alerts"):
        set_quota("pipe", max_alerts=0)


def test_set_quota_negative_window_raises():
    with pytest.raises(ValueError, match="window_seconds"):
        set_quota("pipe", max_alerts=1, window_seconds=-1)


def test_get_quota_returns_none_when_missing():
    assert get_quota("unknown") is None


def test_get_quota_returns_copy():
    set_quota("pipe", max_alerts=2)
    r1 = get_quota("pipe")
    r1["max_alerts"] = 999
    assert get_quota("pipe")["max_alerts"] == 2


def test_remove_quota_returns_true_when_present():
    set_quota("pipe", max_alerts=3)
    assert remove_quota("pipe") is True


def test_remove_quota_returns_false_when_absent():
    assert remove_quota("ghost") is False


def test_list_quotas_reflects_all_rules():
    set_quota("a", max_alerts=1)
    set_quota("b", max_alerts=2)
    names = {r["pipeline"] for r in list_quotas()}
    assert names == {"a", "b"}


def test_is_quota_exceeded_false_when_no_quota():
    assert is_quota_exceeded("noquota") is False


def test_is_quota_exceeded_false_below_limit():
    set_quota("pipe", max_alerts=3, window_seconds=60)
    record_alert("pipe")
    record_alert("pipe")
    assert is_quota_exceeded("pipe") is False


def test_is_quota_exceeded_true_at_limit():
    set_quota("pipe", max_alerts=2, window_seconds=60)
    record_alert("pipe")
    record_alert("pipe")
    assert is_quota_exceeded("pipe") is True


def test_remaining_returns_none_for_unknown_pipeline():
    assert remaining("ghost") is None


def test_remaining_decrements_with_alerts():
    set_quota("pipe", max_alerts=5, window_seconds=3600)
    record_alert("pipe")
    record_alert("pipe")
    assert remaining("pipe") == 3


def test_remaining_does_not_go_below_zero():
    set_quota("pipe", max_alerts=1, window_seconds=3600)
    record_alert("pipe")
    record_alert("pipe")
    assert remaining("pipe") == 0


def test_clear_counts_resets_alert_history():
    set_quota("pipe", max_alerts=1, window_seconds=3600)
    record_alert("pipe")
    assert is_quota_exceeded("pipe") is True
    clear_counts("pipe")
    assert is_quota_exceeded("pipe") is False


def test_overwrite_quota_updates_limit():
    set_quota("pipe", max_alerts=2)
    set_quota("pipe", max_alerts=10)
    assert get_quota("pipe")["max_alerts"] == 10
