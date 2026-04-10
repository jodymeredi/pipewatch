"""Tests for pipewatch/reporter.py"""

from __future__ import annotations

import io
import json
from unittest.mock import patch

import pytest

from pipewatch.metrics import PipelineMetric
from pipewatch.reporter import format_json, format_text, render_report


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_metrics():
    return [
        PipelineMetric("etl_orders", "row_count", 1500.0, "ok", "2024-01-01T00:00:00Z"),
        PipelineMetric("etl_orders", "latency_s", 42.0, "warning", "2024-01-01T00:00:00Z"),
        PipelineMetric("etl_users", "error_rate", 0.12, "critical", "2024-01-01T00:00:00Z"),
    ]


# ---------------------------------------------------------------------------
# format_text
# ---------------------------------------------------------------------------

def test_format_text_contains_pipeline_names(sample_metrics):
    report = format_text(sample_metrics, {"total": 3, "ok": 1, "warning": 1, "critical": 1})
    assert "etl_orders" in report
    assert "etl_users" in report


def test_format_text_contains_status_icons(sample_metrics):
    report = format_text(sample_metrics, {"total": 3, "ok": 1, "warning": 1, "critical": 1})
    assert "✓" in report
    assert "!" in report
    assert "✗" in report


def test_format_text_contains_summary_counts(sample_metrics):
    summary = {"total": 3, "ok": 1, "warning": 1, "critical": 1}
    report = format_text(sample_metrics, summary)
    assert "Total: 3" in report
    assert "Warning: 1" in report
    assert "Critical: 1" in report


def test_format_text_includes_tags():
    m = PipelineMetric(
        "etl_sales", "row_count", 99.0, "ok", "2024-01-01T00:00:00Z",
        tags={"env": "prod"},
    )
    report = format_text([m], {"total": 1, "ok": 1, "warning": 0, "critical": 0})
    assert "env:prod" in report


# ---------------------------------------------------------------------------
# format_json
# ---------------------------------------------------------------------------

def test_format_json_is_valid_json(sample_metrics):
    summary = {"total": 3, "ok": 1, "warning": 1, "critical": 1}
    raw = format_json(sample_metrics, summary)
    data = json.loads(raw)  # must not raise
    assert data["summary"]["total"] == 3


def test_format_json_contains_all_metrics(sample_metrics):
    summary = {"total": 3, "ok": 1, "warning": 1, "critical": 1}
    data = json.loads(format_json(sample_metrics, summary))
    assert len(data["metrics"]) == 3


def test_format_json_metric_fields(sample_metrics):
    summary = {"total": 3, "ok": 1, "warning": 1, "critical": 1}
    data = json.loads(format_json(sample_metrics, summary))
    first = data["metrics"][0]
    assert {"pipeline", "metric_name", "value", "status", "timestamp", "tags"} <= first.keys()


# ---------------------------------------------------------------------------
# render_report
# ---------------------------------------------------------------------------

def test_render_report_writes_to_output(sample_metrics):
    buf = io.StringIO()
    render_report(sample_metrics, fmt="text", output=buf)
    output = buf.getvalue()
    assert "PipeWatch Report" in output


def test_render_report_json_format(sample_metrics):
    buf = io.StringIO()
    render_report(sample_metrics, fmt="json", output=buf)
    data = json.loads(buf.getvalue())
    assert "metrics" in data


def test_render_report_returns_rendered_string(sample_metrics):
    buf = io.StringIO()
    result = render_report(sample_metrics, fmt="text", output=buf)
    assert isinstance(result, str)
    assert len(result) > 0
