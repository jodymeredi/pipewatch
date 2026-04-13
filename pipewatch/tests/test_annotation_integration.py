"""Integration tests: annotations enriching alert dispatch context."""

import pytest
import pipewatch.annotation as ann
from pipewatch.metrics import collect_metric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    ann.clear_all()
    yield
    ann.clear_all()


def _make_metric(pipeline: str, value: float):
    return collect_metric(pipeline, value)


def test_annotations_returned_for_breaching_pipeline():
    """Annotations attached to a pipeline are retrievable after breach."""
    ann.add_annotation("orders_etl", "Known issue: upstream DB latency", author="ops")
    metric = _make_metric("orders_etl", 95.0)
    thresholds = {"orders_etl": {"warning": 80.0, "critical": 90.0}}
    breaches = evaluate_thresholds([metric], thresholds)
    assert any(b.pipeline == "orders_etl" for b in breaches)
    notes = ann.get_annotations("orders_etl")
    assert len(notes) == 1
    assert "upstream DB latency" in notes[0]["note"]


def test_multiple_pipelines_have_independent_annotations():
    ann.add_annotation("pipe_a", "Note for A")
    ann.add_annotation("pipe_b", "Note for B")
    assert ann.get_annotations("pipe_a")[0]["note"] == "Note for A"
    assert ann.get_annotations("pipe_b")[0]["note"] == "Note for B"


def test_search_across_multiple_pipelines():
    ann.add_annotation("pipe_a", "Rollback after hotfix")
    ann.add_annotation("pipe_b", "Hotfix deployed for timeout issue")
    ann.add_annotation("pipe_c", "Routine checkpoint")
    results = ann.search_annotations("hotfix")
    pipelines = {r["pipeline"] for r in results}
    assert pipelines == {"pipe_a", "pipe_b"}


def test_annotation_survives_multiple_metric_collections():
    ann.add_annotation("stable_pipe", "Baseline established")
    for v in [10.0, 12.0, 11.5]:
        _make_metric("stable_pipe", v)
    notes = ann.get_annotations("stable_pipe")
    assert len(notes) == 1
