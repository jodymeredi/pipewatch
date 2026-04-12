"""Tests for pipewatch.runbook."""

from __future__ import annotations

import pytest

import pipewatch.runbook as rb


@pytest.fixture(autouse=True)
def reset_registry():
    rb._registry.clear()
    yield
    rb._registry.clear()


# ---------------------------------------------------------------------------
# set_runbook
# ---------------------------------------------------------------------------

def test_set_runbook_returns_dict_with_url():
    result = rb.set_runbook("etl_daily", url="https://wiki/etl_daily")
    assert result["url"] == "https://wiki/etl_daily"
    assert result["pipeline"] == "etl_daily"


def test_set_runbook_notes_only():
    result = rb.set_runbook("etl_daily", notes="Check S3 bucket permissions.")
    assert result["notes"] == "Check S3 bucket permissions."
    assert result["url"] == ""


def test_set_runbook_both_url_and_notes():
    result = rb.set_runbook("pipe_x", url="https://wiki/x", notes="See Confluence.")
    assert result["url"] == "https://wiki/x"
    assert result["notes"] == "See Confluence."


def test_set_runbook_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline name"):
        rb.set_runbook("   ", url="https://example.com")


def test_set_runbook_no_url_or_notes_raises():
    with pytest.raises(ValueError, match="at least one"):
        rb.set_runbook("pipe_x")


def test_set_runbook_overwrites_previous():
    rb.set_runbook("pipe_x", url="https://old")
    rb.set_runbook("pipe_x", url="https://new")
    assert rb.get_runbook("pipe_x")["url"] == "https://new"


# ---------------------------------------------------------------------------
# get_runbook
# ---------------------------------------------------------------------------

def test_get_runbook_returns_none_when_missing():
    assert rb.get_runbook("unknown") is None


def test_get_runbook_returns_copy():
    rb.set_runbook("pipe_x", url="https://wiki")
    r1 = rb.get_runbook("pipe_x")
    r1["url"] = "mutated"
    assert rb.get_runbook("pipe_x")["url"] == "https://wiki"


# ---------------------------------------------------------------------------
# remove_runbook
# ---------------------------------------------------------------------------

def test_remove_runbook_returns_true_when_present():
    rb.set_runbook("pipe_x", url="https://wiki")
    assert rb.remove_runbook("pipe_x") is True
    assert rb.get_runbook("pipe_x") is None


def test_remove_runbook_returns_false_when_absent():
    assert rb.remove_runbook("nonexistent") is False


# ---------------------------------------------------------------------------
# list_runbooks
# ---------------------------------------------------------------------------

def test_list_runbooks_empty():
    assert rb.list_runbooks() == []


def test_list_runbooks_returns_all_entries():
    rb.set_runbook("pipe_a", url="https://a")
    rb.set_runbook("pipe_b", notes="Check logs.")
    names = {e["pipeline"] for e in rb.list_runbooks()}
    assert names == {"pipe_a", "pipe_b"}


# ---------------------------------------------------------------------------
# enrich_alert
# ---------------------------------------------------------------------------

def test_enrich_alert_adds_runbook_fields():
    rb.set_runbook("pipe_x", url="https://wiki", notes="Restart job.")
    alert = {"pipeline": "pipe_x", "level": "critical"}
    enriched = rb.enrich_alert("pipe_x", alert)
    assert enriched["runbook_url"] == "https://wiki"
    assert enriched["runbook_notes"] == "Restart job."


def test_enrich_alert_unchanged_when_no_runbook():
    alert = {"pipeline": "pipe_y", "level": "warning"}
    enriched = rb.enrich_alert("pipe_y", alert)
    assert "runbook_url" not in enriched
    assert "runbook_notes" not in enriched
