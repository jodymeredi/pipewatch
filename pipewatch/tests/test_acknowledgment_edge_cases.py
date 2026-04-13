"""Edge-case tests for pipewatch.acknowledgment."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

import pipewatch.acknowledgment as ack_mod
from pipewatch.acknowledgment import acknowledge, is_acknowledged, list_acknowledgments


@pytest.fixture(autouse=True)
def reset_registry():
    ack_mod._registry.clear()
    yield
    ack_mod._registry.clear()


def test_level_case_insensitive():
    result = acknowledge("pipe_a", "WARNING", "alice")
    assert result["level"] == "warning"
    assert is_acknowledged("pipe_a", "warning") is True


def test_pipeline_name_stripped():
    result = acknowledge("  pipe_a  ", "ok", "bob")
    assert result["pipeline"] == "pipe_a"


def test_note_stored_stripped():
    result = acknowledge("pipe_a", "ok", "carol", note="  all good  ")
    assert result["note"] == "all good"


def test_expires_at_none_by_default():
    result = acknowledge("pipe_a", "warning", "dave")
    assert result["expires_at"] is None


def test_expired_entry_removed_from_registry():
    past = datetime.now(timezone.utc) - timedelta(seconds=1)
    acknowledge("pipe_a", "critical", "eve", expires_at=past)
    is_acknowledged("pipe_a", "critical")  # triggers cleanup
    assert "pipe_a" not in ack_mod._registry


def test_list_acknowledgments_returns_copies():
    acknowledge("pipe_a", "warning", "frank")
    entries = list_acknowledgments()
    entries[0]["pipeline"] = "tampered"
    assert ack_mod._registry["pipe_a"]["pipeline"] == "pipe_a"


def test_each_acknowledgment_has_unique_id():
    acknowledge("pipe_a", "warning", "grace")
    id1 = ack_mod._registry["pipe_a"]["id"]
    acknowledge("pipe_a", "critical", "grace")
    id2 = ack_mod._registry["pipe_a"]["id"]
    assert id1 != id2
