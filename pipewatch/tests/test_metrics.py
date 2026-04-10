"""Tests for pipewatch.metrics module."""

import pytest
from pipewatch.metrics import (
    PipelineMetric,
    collect_metric,
    evaluate_thresholds,
    summarize_metrics,
)


def test_collect_metric_returns_pipeline_metric():
    metric = collect_metric("row_count", 1500.0)
    assert isinstance(metric, PipelineMetric)
    assert metric.name == "row_count"
    assert metric.value == 1500.0
    assert metric.tags == {}
    assert metric.timestamp > 0


def test_collect_metric_with_tags():
    metric = collect_metric("latency_ms", 320.0, tags={"pipeline": "orders"})
    assert metric.tags == {"pipeline": "orders"}


def test_metric_as_dict():
    metric = collect_metric("error_rate", 0.05, tags={"env": "prod"})
    d = metric.as_dict()
    assert d["name"] == "error_rate"
    assert d["value"] == 0.05
    assert d["tags"] == {"env": "prod"}
    assert "timestamp" in d


def test_evaluate_thresholds_no_breach():
    metric = collect_metric("row_count", 100.0)
    breaches = evaluate_thresholds(metric, {"warning": 500, "critical": 1000})
    assert breaches == []


def test_evaluate_thresholds_warning_breach():
    metric = collect_metric("row_count", 600.0)
    breaches = evaluate_thresholds(metric, {"warning": 500, "critical": 1000})
    assert breaches == ["warning"]


def test_evaluate_thresholds_critical_breach():
    metric = collect_metric("row_count", 1200.0)
    breaches = evaluate_thresholds(metric, {"warning": 500, "critical": 1000})
    assert breaches == ["critical"]


def test_evaluate_thresholds_only_critical_defined():
    metric = collect_metric("latency_ms", 900.0)
    breaches = evaluate_thresholds(metric, {"critical": 800})
    assert breaches == ["critical"]


def test_evaluate_thresholds_empty_config():
    metric = collect_metric("latency_ms", 9999.0)
    breaches = evaluate_thresholds(metric, {})
    assert breaches == []


def test_summarize_metrics_empty():
    assert summarize_metrics([]) == {}


def test_summarize_metrics_values():
    metrics = [
        collect_metric("row_count", 100.0),
        collect_metric("row_count", 200.0),
        collect_metric("row_count", 300.0),
    ]
    summary = summarize_metrics(metrics)
    assert summary["count"] == 3
    assert summary["min"] == 100.0
    assert summary["max"] == 300.0
    assert summary["avg"] == 200.0
    assert summary["latest"] == 300.0
