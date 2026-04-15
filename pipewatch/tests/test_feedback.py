"""Tests for pipewatch/feedback.py"""
import pytest

import pipewatch.feedback as fb


@pytest.fixture(autouse=True)
def reset_registry():
    fb._registry.clear()
    yield
    fb._registry.clear()


def test_record_feedback_returns_dict():
    result = fb.record_feedback("etl_daily", "resolved", note="fixed upstream")
    assert result["pipeline"] == "etl_daily"
    assert result["status"] == "resolved"
    assert result["note"] == "fixed upstream"
    assert result["author"] == "system"
    assert result["recorded_at"].endswith("Z")


def test_record_feedback_custom_author():
    result = fb.record_feedback("etl_daily", "false_positive", author="alice")
    assert result["author"] == "alice"


def test_record_feedback_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        fb.record_feedback("  ", "resolved")


def test_record_feedback_invalid_status_raises():
    with pytest.raises(ValueError, match="status must be one of"):
        fb.record_feedback("etl_daily", "ignored")


def test_record_feedback_status_case_insensitive():
    result = fb.record_feedback("etl_daily", "RESOLVED")
    assert result["status"] == "resolved"


def test_record_feedback_overwrites_previous():
    fb.record_feedback("etl_daily", "needs_investigation")
    fb.record_feedback("etl_daily", "resolved")
    assert fb.get_feedback("etl_daily")["status"] == "resolved"


def test_get_feedback_returns_none_when_missing():
    assert fb.get_feedback("nonexistent") is None


def test_get_feedback_returns_copy():
    fb.record_feedback("etl_daily", "resolved")
    entry = fb.get_feedback("etl_daily")
    entry["status"] = "MUTATED"
    assert fb.get_feedback("etl_daily")["status"] == "resolved"


def test_clear_feedback_returns_true_when_present():
    fb.record_feedback("etl_daily", "resolved")
    assert fb.clear_feedback("etl_daily") is True
    assert fb.get_feedback("etl_daily") is None


def test_clear_feedback_returns_false_when_missing():
    assert fb.clear_feedback("nonexistent") is False


def test_list_feedback_sorted_by_pipeline():
    fb.record_feedback("zzz_pipe", "resolved")
    fb.record_feedback("aaa_pipe", "false_positive")
    names = [e["pipeline"] for e in fb.list_feedback()]
    assert names == ["aaa_pipe", "zzz_pipe"]


def test_list_feedback_empty():
    assert fb.list_feedback() == []


def test_pipelines_by_status_filters_correctly():
    fb.record_feedback("pipe_a", "resolved")
    fb.record_feedback("pipe_b", "false_positive")
    fb.record_feedback("pipe_c", "resolved")
    result = fb.pipelines_by_status("resolved")
    assert set(result) == {"pipe_a", "pipe_c"}


def test_pipelines_by_status_empty_when_none_match():
    fb.record_feedback("pipe_a", "resolved")
    assert fb.pipelines_by_status("false_positive") == []


def test_blank_author_defaults_to_system():
    result = fb.record_feedback("etl_daily", "resolved", author="   ")
    assert result["author"] == "system"
