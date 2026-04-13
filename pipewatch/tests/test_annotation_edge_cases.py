"""Edge-case tests for pipewatch.annotation."""

import pytest
import pipewatch.annotation as ann


@pytest.fixture(autouse=True)
def reset_registry():
    ann.clear_all()
    yield
    ann.clear_all()


def test_empty_tags_list_stored_as_empty():
    result = ann.add_annotation("pipe", "note", tags=[])
    assert result["tags"] == []


def test_none_tags_defaults_to_empty_list():
    result = ann.add_annotation("pipe", "note", tags=None)
    assert result["tags"] == []


def test_blank_author_defaults_to_system():
    result = ann.add_annotation("pipe", "note", author="   ")
    assert result["author"] == "system"


def test_note_is_stripped():
    result = ann.add_annotation("pipe", "  trimmed note  ")
    assert result["note"] == "trimmed note"


def test_created_at_is_monotonically_increasing():
    r1 = ann.add_annotation("pipe", "first")
    r2 = ann.add_annotation("pipe", "second")
    assert r2["created_at"] >= r1["created_at"]


def test_remove_then_add_starts_fresh():
    ann.add_annotation("pipe", "old note")
    ann.remove_annotations("pipe")
    ann.add_annotation("pipe", "new note")
    notes = ann.get_annotations("pipe")
    assert len(notes) == 1
    assert notes[0]["note"] == "new note"


def test_search_empty_registry_returns_empty():
    assert ann.search_annotations("anything") == []


def test_list_annotated_pipelines_empty_when_none_added():
    assert ann.list_annotated_pipelines() == []


def test_tags_are_sorted_alphabetically():
    result = ann.add_annotation("pipe", "note", tags=["z", "a", "m"])
    assert result["tags"] == ["a", "m", "z"]
