"""Edge-case tests for pipewatch.priority."""

import pytest

from pipewatch.priority import (
    clear_priorities,
    list_priorities,
    set_priority,
    sort_by_priority,
)


@pytest.fixture(autouse=True)
def reset_registry():
    clear_priorities()
    yield
    clear_priorities()


def test_set_priority_strips_whitespace_in_name():
    result = set_priority("  ingest  ", 10)
    assert result["pipeline"] == "ingest"


def test_list_priorities_returns_copies_not_references():
    set_priority("ingest", 10)
    lst = list_priorities()
    lst[0]["priority"] = 999
    # Original registry should be unaffected
    assert list_priorities()[0]["priority"] == 10


def test_sort_by_priority_empty_list():
    assert sort_by_priority([]) == []


def test_sort_by_priority_single_item():
    result = sort_by_priority(["only"])
    assert result == ["only"]


def test_overwrite_priority_reflected_in_list():
    set_priority("ingest", 30)
    set_priority("ingest", 5)
    entries = list_priorities()
    assert len(entries) == 1
    assert entries[0]["priority"] == 5


def test_negative_priority_raises():
    with pytest.raises(ValueError):
        set_priority("ingest", -1)


def test_empty_string_pipeline_raises():
    with pytest.raises(ValueError):
        set_priority("", 10)


def test_multiple_pipelines_independent():
    set_priority("a", 1)
    set_priority("b", 99)
    assert list_priorities()[0]["pipeline"] == "a"
    assert list_priorities()[1]["pipeline"] == "b"
