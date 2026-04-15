"""Integration tests: feedback interacting with metrics and dispatch simulation."""
import pytest

import pipewatch.feedback as fb
from pipewatch.metrics import PipelineMetric


@pytest.fixture(autouse=True)
def reset():
    fb._registry.clear()
    yield
    fb._registry.clear()


def _make_metric(pipeline: str, status: str = "warning") -> PipelineMetric:
    return PipelineMetric(
        pipeline=pipeline,
        value=42.0,
        status=status,
        tags={},
        thresholds={},
    )


def test_false_positive_pipelines_excluded_from_dispatch_simulation():
    metrics = [
        _make_metric("pipe_a", "critical"),
        _make_metric("pipe_b", "warning"),
        _make_metric("pipe_c", "critical"),
    ]
    fb.record_feedback("pipe_a", "false_positive")

    false_positives = set(fb.pipelines_by_status("false_positive"))
    actionable = [m for m in metrics if m.pipeline not in false_positives]

    assert len(actionable) == 2
    assert all(m.pipeline != "pipe_a" for m in actionable)


def test_resolved_pipelines_tracked_independently():
    fb.record_feedback("pipe_x", "resolved", note="upstream fix deployed", author="bob")
    fb.record_feedback("pipe_y", "needs_investigation")

    resolved = fb.pipelines_by_status("resolved")
    investigating = fb.pipelines_by_status("needs_investigation")

    assert resolved == ["pipe_x"]
    assert investigating == ["pipe_y"]


def test_clearing_feedback_re_exposes_pipeline():
    metrics = [_make_metric("pipe_a", "critical")]
    fb.record_feedback("pipe_a", "false_positive")

    false_positives = set(fb.pipelines_by_status("false_positive"))
    assert "pipe_a" in false_positives

    fb.clear_feedback("pipe_a")
    false_positives = set(fb.pipelines_by_status("false_positive"))
    actionable = [m for m in metrics if m.pipeline not in false_positives]
    assert len(actionable) == 1
    assert actionable[0].pipeline == "pipe_a"


def test_multiple_pipelines_independent_feedback():
    for name in ["alpha", "beta", "gamma"]:
        fb.record_feedback(name, "resolved", author="ops")

    entries = fb.list_feedback()
    assert len(entries) == 3
    assert all(e["status"] == "resolved" for e in entries)
    assert all(e["author"] == "ops" for e in entries)
