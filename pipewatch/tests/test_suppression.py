"""Tests for pipewatch/suppression.py"""
import pytest

import pipewatch.suppression as sup
from pipewatch.suppression import (
    add_suppression,
    clear_all_suppressions,
    get_suppression,
    is_suppressed,
    list_suppressions,
    remove_suppression,
)


@pytest.fixture(autouse=True)
def reset_registry():
    clear_all_suppressions()
    yield
    clear_all_suppressions()


# ---------------------------------------------------------------------------
# add_suppression
# ---------------------------------------------------------------------------

def test_add_suppression_returns_rule_dict():
    rule = add_suppression("pipe_a", ["warning"], reason="planned maintenance")
    assert rule["pipeline"] == "pipe_a"
    assert rule["levels"] == ["warning"]
    assert rule["reason"] == "planned maintenance"
    assert "created_at" in rule


def test_add_suppression_deduplicates_levels():
    rule = add_suppression("pipe_b", ["warning", "warning", "critical"])
    assert rule["levels"] == ["critical", "warning"]  # sorted + deduped


def test_add_suppression_invalid_level_raises():
    with pytest.raises(ValueError, match="Invalid suppression levels"):
        add_suppression("pipe_c", ["unknown"])


def test_add_suppression_empty_levels_raises():
    with pytest.raises(ValueError, match="levels must contain"):
        add_suppression("pipe_d", [])


def test_add_suppression_overwrites_existing_rule():
    add_suppression("pipe_e", ["warning"])
    add_suppression("pipe_e", ["critical"])
    rule = get_suppression("pipe_e")
    assert rule["levels"] == ["critical"]


# ---------------------------------------------------------------------------
# is_suppressed
# ---------------------------------------------------------------------------

def test_is_suppressed_returns_false_for_unknown_pipeline():
    assert is_suppressed("no_such_pipe", "warning") is False


def test_is_suppressed_true_when_level_matches():
    add_suppression("pipe_f", ["warning"])
    assert is_suppressed("pipe_f", "warning") is True


def test_is_suppressed_false_when_level_not_in_rule():
    add_suppression("pipe_g", ["warning"])
    assert is_suppressed("pipe_g", "critical") is False


def test_is_suppressed_ok_level():
    add_suppression("pipe_h", ["ok", "warning"])
    assert is_suppressed("pipe_h", "ok") is True


# ---------------------------------------------------------------------------
# remove_suppression
# ---------------------------------------------------------------------------

def test_remove_suppression_returns_true_when_existed():
    add_suppression("pipe_i", ["warning"])
    assert remove_suppression("pipe_i") is True


def test_remove_suppression_returns_false_when_not_found():
    assert remove_suppression("ghost_pipe") is False


def test_remove_suppression_clears_rule():
    add_suppression("pipe_j", ["warning"])
    remove_suppression("pipe_j")
    assert get_suppression("pipe_j") is None


# ---------------------------------------------------------------------------
# list_suppressions / get_suppression
# ---------------------------------------------------------------------------

def test_list_suppressions_reflects_added_rules():
    add_suppression("pipe_k", ["warning"])
    add_suppression("pipe_l", ["critical"])
    names = {r["pipeline"] for r in list_suppressions()}
    assert names == {"pipe_k", "pipe_l"}


def test_list_suppressions_returns_copies():
    add_suppression("pipe_m", ["warning"])
    rules = list_suppressions()
    rules[0]["levels"] = []
    # original should be unaffected
    assert get_suppression("pipe_m")["levels"] == ["warning"]
