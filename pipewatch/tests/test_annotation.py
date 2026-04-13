"""Unit tests for pipewatch.annotation."""

import pytest
import pipewatch.annotation as ann


@pytest.fixture(autouse=True)
def reset_registry():
    ann.clear_all()
    yield
    ann.clear_all()


# ---------------------------------------------------------------------------
# add_annotation
# ---------------------------------------------------------------------------

def test_add_annotation_returns_dict():
    result = ann.add_annotation("etl_orders", "Deployed hotfix v2.3")
    assert result["pipeline"] == "etl_orders"
    assert result["note"] == "Deployed hotfix v2.3"
    assert result["author"] == "system"
    assert isinstance(result["created_at"], float)


def test_add_annotation_with_author_and_tags():
    result = ann.add_annotation(
        "etl_orders", "Performance tuning", author="alice", tags=["perf", "prod"]
    )
    assert result["author"] == "alice"
    assert result["tags"] == ["perf", "prod"]


def test_add_annotation_deduplicates_tags():
    result = ann.add_annotation("pipe", "note", tags=["a", "a", "b"])
    assert result["tags"] == ["a", "b"]


def test_add_annotation_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline"):
        ann.add_annotation("  ", "some note")


def test_add_annotation_blank_note_raises():
    with pytest.raises(ValueError, match="note"):
        ann.add_annotation("pipe", "   ")


def test_add_annotation_strips_whitespace_from_pipeline():
    ann.add_annotation("  pipe  ", "note")
    assert "pipe" in ann.list_annotated_pipelines()


# ---------------------------------------------------------------------------
# get_annotations
# ---------------------------------------------------------------------------

def test_get_annotations_returns_empty_for_unknown():
    assert ann.get_annotations("unknown") == []


def test_get_annotations_returns_all_entries():
    ann.add_annotation("pipe", "first")
    ann.add_annotation("pipe", "second")
    results = ann.get_annotations("pipe")
    assert len(results) == 2
    assert results[0]["note"] == "first"
    assert results[1]["note"] == "second"


def test_get_annotations_returns_copies():
    ann.add_annotation("pipe", "note")
    results = ann.get_annotations("pipe")
    results[0]["note"] = "mutated"
    assert ann.get_annotations("pipe")[0]["note"] == "note"


# ---------------------------------------------------------------------------
# remove_annotations
# ---------------------------------------------------------------------------

def test_remove_annotations_returns_count():
    ann.add_annotation("pipe", "a")
    ann.add_annotation("pipe", "b")
    count = ann.remove_annotations("pipe")
    assert count == 2
    assert ann.get_annotations("pipe") == []


def test_remove_annotations_unknown_pipeline_returns_zero():
    assert ann.remove_annotations("ghost") == 0


# ---------------------------------------------------------------------------
# list_annotated_pipelines
# ---------------------------------------------------------------------------

def test_list_annotated_pipelines_sorted():
    ann.add_annotation("zzz", "note")
    ann.add_annotation("aaa", "note")
    assert ann.list_annotated_pipelines() == ["aaa", "zzz"]


def test_list_annotated_pipelines_excludes_cleared():
    ann.add_annotation("pipe", "note")
    ann.remove_annotations("pipe")
    assert "pipe" not in ann.list_annotated_pipelines()


# ---------------------------------------------------------------------------
# search_annotations
# ---------------------------------------------------------------------------

def test_search_annotations_finds_keyword():
    ann.add_annotation("pipe", "Deployed hotfix v2.3")
    ann.add_annotation("other", "Routine maintenance")
    results = ann.search_annotations("hotfix")
    assert len(results) == 1
    assert results[0]["pipeline"] == "pipe"


def test_search_annotations_case_insensitive():
    ann.add_annotation("pipe", "Critical alert triggered")
    results = ann.search_annotations("CRITICAL")
    assert len(results) == 1


def test_search_annotations_no_match_returns_empty():
    ann.add_annotation("pipe", "nothing relevant")
    assert ann.search_annotations("hotfix") == []
