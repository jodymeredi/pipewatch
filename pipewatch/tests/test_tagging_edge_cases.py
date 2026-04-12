"""Edge-case tests for pipewatch.tagging."""

import pytest

from pipewatch.tagging import (
    tag_pipeline,
    untag_pipeline,
    get_tags,
    list_tags,
    clear_registry,
    pipelines_for_tag,
)


@pytest.fixture(autouse=True)
def reset_registry():
    clear_registry()
    yield
    clear_registry()


def test_tagging_same_tag_twice_is_idempotent():
    tag_pipeline("etl_orders", ["env:prod"])
    tag_pipeline("etl_orders", ["env:prod"])
    assert get_tags("etl_orders").count("env:prod") == 1


def test_untag_nonexistent_tag_returns_false():
    tag_pipeline("etl_orders", ["env:prod"])
    removed = untag_pipeline("etl_orders", ["env:staging"])
    assert removed is False


def test_list_tags_excludes_empty_sets_after_untag():
    tag_pipeline("etl_orders", ["env:prod"])
    untag_pipeline("etl_orders", ["env:prod"])
    tags = list_tags()
    assert "env:prod" not in tags


def test_whitespace_only_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline name"):
        tag_pipeline("   ", ["env:prod"])


def test_tag_multiple_pipelines_index_correct():
    tag_pipeline("pipe_a", ["team:data"])
    tag_pipeline("pipe_b", ["team:data"])
    tag_pipeline("pipe_c", ["team:infra"])

    data_pipes = pipelines_for_tag("team:data")
    assert "pipe_a" in data_pipes
    assert "pipe_b" in data_pipes
    assert "pipe_c" not in data_pipes


def test_get_tags_returns_sorted():
    tag_pipeline("etl_orders", ["zzz:last", "aaa:first", "mmm:mid"])
    tags = get_tags("etl_orders")
    assert tags == sorted(tags)


def test_clear_registry_removes_all_state():
    tag_pipeline("etl_orders", ["env:prod"])
    clear_registry()
    assert get_tags("etl_orders") == []
    assert pipelines_for_tag("env:prod") == []
    assert list_tags() == {}
