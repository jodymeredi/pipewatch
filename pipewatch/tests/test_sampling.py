"""Tests for pipewatch.sampling."""

from __future__ import annotations

import pytest

import pipewatch.sampling as sampling
from pipewatch.metrics import collect_metric


@pytest.fixture(autouse=True)
def reset_registry():
    sampling._registry.clear()
    yield
    sampling._registry.clear()


def _make_metric(name: str, value: float = 1.0):
    return collect_metric(name, value)


# --- set_sample_rate ---

def test_set_sample_rate_returns_dict():
    result = sampling.set_sample_rate("pipe_a", 0.5)
    assert result == {"pipeline": "pipe_a", "rate": 0.5}


def test_set_sample_rate_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        sampling.set_sample_rate("  ", 0.5)


def test_set_sample_rate_zero_raises():
    with pytest.raises(ValueError, match="range"):
        sampling.set_sample_rate("pipe_a", 0.0)


def test_set_sample_rate_above_one_raises():
    with pytest.raises(ValueError, match="range"):
        sampling.set_sample_rate("pipe_a", 1.1)


def test_set_sample_rate_one_is_valid():
    result = sampling.set_sample_rate("pipe_a", 1.0)
    assert result["rate"] == 1.0


# --- get_sample_rate ---

def test_get_sample_rate_returns_default_for_unknown():
    assert sampling.get_sample_rate("unknown") == 1.0


def test_get_sample_rate_returns_configured_value():
    sampling.set_sample_rate("pipe_a", 0.25)
    assert sampling.get_sample_rate("pipe_a") == 0.25


# --- remove_sample_rate ---

def test_remove_sample_rate_returns_true_when_present():
    sampling.set_sample_rate("pipe_a", 0.5)
    assert sampling.remove_sample_rate("pipe_a") is True


def test_remove_sample_rate_returns_false_when_absent():
    assert sampling.remove_sample_rate("pipe_a") is False


def test_remove_sample_rate_falls_back_to_default():
    sampling.set_sample_rate("pipe_a", 0.1)
    sampling.remove_sample_rate("pipe_a")
    assert sampling.get_sample_rate("pipe_a") == 1.0


# --- list_sample_rates ---

def test_list_sample_rates_empty_when_no_rules():
    assert sampling.list_sample_rates() == []


def test_list_sample_rates_reflects_registered_rules():
    sampling.set_sample_rate("pipe_a", 0.5)
    sampling.set_sample_rate("pipe_b", 0.8)
    names = {r["pipeline"] for r in sampling.list_sample_rates()}
    assert names == {"pipe_a", "pipe_b"}


def test_list_sample_rates_returns_copies_not_references():
    sampling.set_sample_rate("pipe_a", 0.5)
    lst = sampling.list_sample_rates()
    lst[0]["rate"] = 0.99
    assert sampling.get_sample_rate("pipe_a") == 0.5


# --- should_sample / filter_sampled_metrics ---

def test_should_sample_always_true_at_rate_one():
    sampling.set_sample_rate("pipe_a", 1.0)
    assert all(sampling.should_sample("pipe_a") for _ in range(20))


def test_filter_sampled_metrics_rate_one_keeps_all():
    sampling.set_sample_rate("pipe_a", 1.0)
    metrics = [_make_metric("pipe_a") for _ in range(5)]
    result = sampling.filter_sampled_metrics(metrics)
    assert len(result) == 5


def test_filter_sampled_metrics_unknown_pipeline_defaults_to_full():
    metrics = [_make_metric("unregistered") for _ in range(5)]
    result = sampling.filter_sampled_metrics(metrics)
    assert len(result) == 5


def test_filter_sampled_metrics_mixed_pipelines():
    sampling.set_sample_rate("always", 1.0)
    sampling.set_sample_rate("never", 0.001)
    metrics = (
        [_make_metric("always") for _ in range(10)]
        + [_make_metric("never") for _ in range(10)]
    )
    result = sampling.filter_sampled_metrics(metrics, seed=42)
    always_kept = [m for m in result if m.pipeline == "always"]
    assert len(always_kept) == 10
