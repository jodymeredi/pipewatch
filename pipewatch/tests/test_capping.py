"""Tests for pipewatch.capping."""

from __future__ import annotations

import pytest

import pipewatch.capping as capping


@pytest.fixture(autouse=True)
def reset_registry():
    capping._registry.clear()
    yield
    capping._registry.clear()


# ---------------------------------------------------------------------------
# set_cap
# ---------------------------------------------------------------------------

def test_set_cap_returns_dict_with_floor_and_ceiling():
    rule = capping.set_cap("pipe_a", floor=0.0, ceiling=100.0)
    assert rule["pipeline"] == "pipe_a"
    assert rule["floor"] == 0.0
    assert rule["ceiling"] == 100.0


def test_set_cap_floor_only():
    rule = capping.set_cap("pipe_b", floor=-10.0)
    assert rule["floor"] == -10.0
    assert rule["ceiling"] is None


def test_set_cap_ceiling_only():
    rule = capping.set_cap("pipe_c", ceiling=50.0)
    assert rule["floor"] is None
    assert rule["ceiling"] == 50.0


def test_set_cap_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        capping.set_cap("  ", floor=0.0)


def test_set_cap_no_bounds_raises():
    with pytest.raises(ValueError, match="at least one"):
        capping.set_cap("pipe_d")


def test_set_cap_floor_equals_ceiling_raises():
    with pytest.raises(ValueError, match="strictly less"):
        capping.set_cap("pipe_e", floor=5.0, ceiling=5.0)


def test_set_cap_floor_greater_than_ceiling_raises():
    with pytest.raises(ValueError, match="strictly less"):
        capping.set_cap("pipe_f", floor=10.0, ceiling=5.0)


def test_set_cap_overwrites_existing():
    capping.set_cap("pipe_g", floor=0.0, ceiling=100.0)
    capping.set_cap("pipe_g", floor=5.0, ceiling=200.0)
    rule = capping.get_cap("pipe_g")
    assert rule["floor"] == 5.0
    assert rule["ceiling"] == 200.0


# ---------------------------------------------------------------------------
# get_cap / remove_cap / list_caps
# ---------------------------------------------------------------------------

def test_get_cap_returns_none_when_missing():
    assert capping.get_cap("nonexistent") is None


def test_get_cap_returns_copy_not_reference():
    capping.set_cap("pipe_h", floor=1.0, ceiling=9.0)
    rule = capping.get_cap("pipe_h")
    rule["floor"] = 999.0
    assert capping.get_cap("pipe_h")["floor"] == 1.0


def test_remove_cap_returns_true_when_present():
    capping.set_cap("pipe_i", ceiling=10.0)
    assert capping.remove_cap("pipe_i") is True
    assert capping.get_cap("pipe_i") is None


def test_remove_cap_returns_false_when_absent():
    assert capping.remove_cap("ghost") is False


def test_list_caps_reflects_all_rules():
    capping.set_cap("p1", floor=0.0)
    capping.set_cap("p2", ceiling=50.0)
    names = {r["pipeline"] for r in capping.list_caps()}
    assert names == {"p1", "p2"}


# ---------------------------------------------------------------------------
# apply_cap
# ---------------------------------------------------------------------------

def test_apply_cap_clamps_above_ceiling():
    capping.set_cap("pipe_j", floor=0.0, ceiling=100.0)
    assert capping.apply_cap("pipe_j", 150.0) == 100.0


def test_apply_cap_clamps_below_floor():
    capping.set_cap("pipe_k", floor=10.0, ceiling=90.0)
    assert capping.apply_cap("pipe_k", 3.0) == 10.0


def test_apply_cap_value_within_bounds_unchanged():
    capping.set_cap("pipe_l", floor=0.0, ceiling=100.0)
    assert capping.apply_cap("pipe_l", 55.0) == 55.0


def test_apply_cap_no_rule_returns_value_unchanged():
    assert capping.apply_cap("unknown_pipe", 999.0) == 999.0


def test_apply_cap_floor_only_does_not_clamp_high_value():
    capping.set_cap("pipe_m", floor=5.0)
    assert capping.apply_cap("pipe_m", 1000.0) == 1000.0
    assert capping.apply_cap("pipe_m", 1.0) == 5.0


def test_apply_cap_ceiling_only_does_not_clamp_low_value():
    capping.set_cap("pipe_n", ceiling=20.0)
    assert capping.apply_cap("pipe_n", -50.0) == -50.0
    assert capping.apply_cap("pipe_n", 25.0) == 20.0
