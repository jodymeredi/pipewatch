"""CLI-style integration tests for annotation workflows."""

import pytest
import pipewatch.annotation as ann


@pytest.fixture(autouse=True)
def reset():
    ann.clear_all()
    yield
    ann.clear_all()


def _simulate_add(pipeline: str, note: str, author: str = "system", tags=None):
    return ann.add_annotation(pipeline, note, author=author, tags=tags)


def _simulate_list(pipeline: str):
    return ann.get_annotations(pipeline)


def _simulate_remove(pipeline: str):
    return ann.remove_annotations(pipeline)


def _simulate_search(keyword: str):
    return ann.search_annotations(keyword)


def test_add_returns_correct_dict():
    result = _simulate_add("etl_pipe", "Deployed v1.0", author="dev")
    assert result["pipeline"] == "etl_pipe"
    assert result["author"] == "dev"
    assert result["note"] == "Deployed v1.0"


def test_list_after_add_returns_entry():
    _simulate_add("etl_pipe", "First note")
    entries = _simulate_list("etl_pipe")
    assert len(entries) == 1
    assert entries[0]["note"] == "First note"


def test_remove_after_add_clears_entries():
    _simulate_add("etl_pipe", "Temp note")
    count = _simulate_remove("etl_pipe")
    assert count == 1
    assert _simulate_list("etl_pipe") == []


def test_search_returns_matching_entries():
    _simulate_add("pipe_a", "hotfix applied")
    _simulate_add("pipe_b", "routine run")
    results = _simulate_search("hotfix")
    assert len(results) == 1
    assert results[0]["pipeline"] == "pipe_a"


def test_list_annotated_pipelines_workflow():
    _simulate_add("alpha", "note")
    _simulate_add("beta", "note")
    pipelines = ann.list_annotated_pipelines()
    assert "alpha" in pipelines
    assert "beta" in pipelines


def test_full_workflow_add_search_remove():
    _simulate_add("pipe", "incident: disk full", author="oncall", tags=["incident"])
    results = _simulate_search("disk")
    assert results[0]["author"] == "oncall"
    assert results[0]["tags"] == ["incident"]
    _simulate_remove("pipe")
    assert _simulate_list("pipe") == []


def test_multiple_annotations_same_pipeline():
    """Adding multiple annotations to the same pipeline should accumulate entries."""
    _simulate_add("shared_pipe", "Initial deploy", author="dev1")
    _simulate_add("shared_pipe", "Config update", author="dev2")
    _simulate_add("shared_pipe", "Hotfix applied", author="dev1")
    entries = _simulate_list("shared_pipe")
    assert len(entries) == 3
    notes = [e["note"] for e in entries]
    assert "Initial deploy" in notes
    assert "Config update" in notes
    assert "Hotfix applied" in notes
