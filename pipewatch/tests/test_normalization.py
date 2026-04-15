"""Tests for pipewatch.normalization."""
import pytest

import pipewatch.normalization as norm


@pytest.fixture(autouse=True)
def reset_registry():
    norm._registry.clear()
    yield
    norm._registry.clear()


# --- set_normalization ---

def test_set_normalization_returns_dict_minmax():
    rule = norm.set_normalization("pipe_a", "minmax", min_val=0.0, max_val=100.0)
    assert rule["pipeline"] == "pipe_a"
    assert rule["method"] == "minmax"
    assert rule["min_val"] == 0.0
    assert rule["max_val"] == 100.0


def test_set_normalization_returns_dict_zscore():
    rule = norm.set_normalization("pipe_b", "zscore", mean=50.0, std=10.0)
    assert rule["method"] == "zscore"
    assert rule["mean"] == 50.0
    assert rule["std"] == 10.0


def test_set_normalization_returns_dict_clamp():
    rule = norm.set_normalization("pipe_c", "clamp", clamp_low=0.0, clamp_high=1.0)
    assert rule["method"] == "clamp"
    assert rule["clamp_low"] == 0.0
    assert rule["clamp_high"] == 1.0


def test_set_normalization_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        norm.set_normalization("  ", "minmax")


def test_set_normalization_invalid_method_raises():
    with pytest.raises(ValueError, match="method"):
        norm.set_normalization("pipe_a", "log")


def test_set_normalization_minmax_equal_bounds_raises():
    with pytest.raises(ValueError, match="differ"):
        norm.set_normalization("pipe_a", "minmax", min_val=5.0, max_val=5.0)


def test_set_normalization_zscore_zero_std_raises():
    with pytest.raises(ValueError, match="non-zero"):
        norm.set_normalization("pipe_a", "zscore", mean=0.0, std=0.0)


# --- get / remove / list ---

def test_get_normalization_returns_none_when_missing():
    assert norm.get_normalization("unknown") is None


def test_get_normalization_returns_copy():
    norm.set_normalization("pipe_a", "minmax", min_val=0.0, max_val=1.0)
    r1 = norm.get_normalization("pipe_a")
    r1["method"] = "tampered"
    assert norm.get_normalization("pipe_a")["method"] == "minmax"


def test_remove_normalization_returns_true_when_present():
    norm.set_normalization("pipe_a", "minmax", min_val=0.0, max_val=1.0)
    assert norm.remove_normalization("pipe_a") is True
    assert norm.get_normalization("pipe_a") is None


def test_remove_normalization_returns_false_when_missing():
    assert norm.remove_normalization("nonexistent") is False


def test_list_normalizations_reflects_all_rules():
    norm.set_normalization("p1", "minmax", min_val=0.0, max_val=10.0)
    norm.set_normalization("p2", "clamp", clamp_low=0.0)
    names = {r["pipeline"] for r in norm.list_normalizations()}
    assert names == {"p1", "p2"}


# --- normalize_value ---

def test_normalize_value_minmax_midpoint():
    norm.set_normalization("pipe_a", "minmax", min_val=0.0, max_val=100.0)
    result, applied = norm.normalize_value("pipe_a", 50.0)
    assert applied is True
    assert abs(result - 0.5) < 1e-9


def test_normalize_value_zscore():
    norm.set_normalization("pipe_b", "zscore", mean=100.0, std=20.0)
    result, applied = norm.normalize_value("pipe_b", 120.0)
    assert applied is True
    assert abs(result - 1.0) < 1e-9


def test_normalize_value_clamp_high():
    norm.set_normalization("pipe_c", "clamp", clamp_low=0.0, clamp_high=1.0)
    result, applied = norm.normalize_value("pipe_c", 5.0)
    assert applied is True
    assert result == 1.0


def test_normalize_value_clamp_low():
    norm.set_normalization("pipe_c", "clamp", clamp_low=0.0, clamp_high=1.0)
    result, applied = norm.normalize_value("pipe_c", -3.0)
    assert result == 0.0


def test_normalize_value_no_rule_returns_original():
    result, applied = norm.normalize_value("unknown_pipe", 42.0)
    assert applied is False
    assert result == 42.0
