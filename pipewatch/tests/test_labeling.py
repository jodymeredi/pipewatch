"""Tests for pipewatch.labeling."""
from __future__ import annotations

import pytest

import pipewatch.labeling as labeling
from pipewatch.labeling import (
    clear_labels,
    get_label,
    get_labels,
    list_labels,
    pipelines_with_label,
    remove_label,
    set_label,
)


@pytest.fixture(autouse=True)
def reset_registry():
    labeling._registry.clear()
    yield
    labeling._registry.clear()


# ---------------------------------------------------------------------------
# set_label
# ---------------------------------------------------------------------------

def test_set_label_returns_label_map():
    result = set_label("pipe_a", "owner", "alice")
    assert result == {"owner": "alice"}


def test_set_label_multiple_keys():
    set_label("pipe_a", "owner", "alice")
    result = set_label("pipe_a", "env", "prod")
    assert result == {"owner": "alice", "env": "prod"}


def test_set_label_overwrites_existing_key():
    set_label("pipe_a", "owner", "alice")
    result = set_label("pipe_a", "owner", "bob")
    assert result["owner"] == "bob"


def test_set_label_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline"):
        set_label("  ", "owner", "alice")


def test_set_label_blank_key_raises():
    with pytest.raises(ValueError, match="key"):
        set_label("pipe_a", "", "alice")


# ---------------------------------------------------------------------------
# get_label / get_labels
# ---------------------------------------------------------------------------

def test_get_label_returns_value():
    set_label("pipe_a", "env", "staging")
    assert get_label("pipe_a", "env") == "staging"


def test_get_label_returns_none_when_missing():
    assert get_label("pipe_a", "env") is None


def test_get_labels_returns_copy():
    set_label("pipe_a", "owner", "alice")
    labels = get_labels("pipe_a")
    labels["owner"] = "tampered"
    assert get_label("pipe_a", "owner") == "alice"


def test_get_labels_empty_for_unknown_pipeline():
    assert get_labels("nonexistent") == {}


# ---------------------------------------------------------------------------
# remove_label
# ---------------------------------------------------------------------------

def test_remove_label_returns_true_when_present():
    set_label("pipe_a", "env", "prod")
    assert remove_label("pipe_a", "env") is True


def test_remove_label_returns_false_when_absent():
    assert remove_label("pipe_a", "env") is False


def test_remove_label_cleans_up_empty_pipeline_entry():
    set_label("pipe_a", "env", "prod")
    remove_label("pipe_a", "env")
    assert "pipe_a" not in list_labels()


# ---------------------------------------------------------------------------
# pipelines_with_label
# ---------------------------------------------------------------------------

def test_pipelines_with_label_key_only():
    set_label("pipe_a", "env", "prod")
    set_label("pipe_b", "env", "staging")
    set_label("pipe_c", "owner", "alice")
    result = pipelines_with_label("env")
    assert sorted(result) == ["pipe_a", "pipe_b"]


def test_pipelines_with_label_key_and_value():
    set_label("pipe_a", "env", "prod")
    set_label("pipe_b", "env", "staging")
    result = pipelines_with_label("env", "prod")
    assert result == ["pipe_a"]


def test_pipelines_with_label_no_match_returns_empty():
    assert pipelines_with_label("nonexistent") == []


# ---------------------------------------------------------------------------
# clear_labels
# ---------------------------------------------------------------------------

def test_clear_labels_returns_count():
    set_label("pipe_a", "env", "prod")
    set_label("pipe_a", "owner", "alice")
    assert clear_labels("pipe_a") == 2


def test_clear_labels_unknown_pipeline_returns_zero():
    assert clear_labels("ghost") == 0
