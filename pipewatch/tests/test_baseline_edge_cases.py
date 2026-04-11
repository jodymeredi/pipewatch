"""Edge-case tests for pipewatch.baseline."""

import pytest
import pipewatch.baseline as bl


@pytest.fixture(autouse=True)
def reset():
    bl.clear_baselines()
    yield
    bl.clear_baselines()


def test_overwrite_baseline_updates_value():
    bl.set_baseline("p", "m", 10.0)
    bl.set_baseline("p", "m", 20.0)
    assert bl.get_baseline("p", "m") == 20.0


def test_negative_baseline_value_accepted():
    bl.set_baseline("p", "delta", -50.0)
    assert bl.get_baseline("p", "delta") == -50.0


def test_compare_negative_baseline_positive_current():
    bl.set_baseline("p", "delta", -100.0)
    result = bl.compare_to_baseline("p", "delta", -90.0, tolerance=0.05)
    # deviation = (-90 - -100) / 100 = 0.1 -> breached at 5% tolerance
    assert result["breached"] is True


def test_compare_exact_match_no_breach():
    bl.set_baseline("p", "m", 42.0)
    result = bl.compare_to_baseline("p", "m", 42.0)
    assert result["deviation"] == 0.0
    assert result["breached"] is False


def test_tolerance_zero_any_deviation_breaches():
    bl.set_baseline("p", "m", 100.0)
    result = bl.compare_to_baseline("p", "m", 100.001, tolerance=0.0)
    assert result["breached"] is True


def test_large_tolerance_never_breaches():
    bl.set_baseline("p", "m", 100.0)
    result = bl.compare_to_baseline("p", "m", 999.0, tolerance=100.0)
    assert result["breached"] is False


def test_list_baselines_returns_copy_not_reference():
    bl.set_baseline("p", "m", 1.0)
    listing = bl.list_baselines()
    listing["p"]["m"] = 999.0
    assert bl.get_baseline("p", "m") == 1.0


def test_remove_nonexistent_metric_from_existing_pipeline():
    bl.set_baseline("p", "m1", 1.0)
    result = bl.remove_baseline("p", "m2")
    assert result is False
    assert bl.get_baseline("p", "m1") == 1.0


def test_clear_baselines_empties_registry():
    bl.set_baseline("a", "x", 1.0)
    bl.set_baseline("b", "y", 2.0)
    bl.clear_baselines()
    assert bl.list_baselines() == {}
