"""Tests for pipewatch.healthcheck."""

from __future__ import annotations

import pytest

import pipewatch.healthcheck as hc


@pytest.fixture(autouse=True)
def reset_registry():
    hc._registry.clear()
    hc._heartbeats.clear()
    yield
    hc._registry.clear()
    hc._heartbeats.clear()


# ---------------------------------------------------------------------------
# register_healthcheck
# ---------------------------------------------------------------------------

def test_register_healthcheck_returns_dict():
    result = hc.register_healthcheck("pipe-a", tolerance_seconds=60)
    assert result["pipeline"] == "pipe-a"
    assert result["tolerance_seconds"] == 60


def test_register_healthcheck_with_label():
    result = hc.register_healthcheck("pipe-a", label="nightly")
    assert result["label"] == "nightly"


def test_register_healthcheck_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        hc.register_healthcheck("   ")


def test_register_healthcheck_zero_tolerance_raises():
    with pytest.raises(ValueError, match="positive"):
        hc.register_healthcheck("pipe-a", tolerance_seconds=0)


def test_register_healthcheck_negative_tolerance_raises():
    with pytest.raises(ValueError, match="positive"):
        hc.register_healthcheck("pipe-a", tolerance_seconds=-10)


def test_register_healthcheck_overwrites_existing():
    hc.register_healthcheck("pipe-a", tolerance_seconds=60)
    hc.register_healthcheck("pipe-a", tolerance_seconds=120)
    assert hc.get_healthcheck("pipe-a")["tolerance_seconds"] == 120


# ---------------------------------------------------------------------------
# remove_healthcheck
# ---------------------------------------------------------------------------

def test_remove_healthcheck_clears_entry():
    hc.register_healthcheck("pipe-a")
    hc.remove_healthcheck("pipe-a")
    assert hc.get_healthcheck("pipe-a") is None


def test_remove_healthcheck_also_clears_heartbeat():
    hc.register_healthcheck("pipe-a")
    hc.record_heartbeat("pipe-a")
    hc.remove_healthcheck("pipe-a")
    assert "pipe-a" not in hc._heartbeats


# ---------------------------------------------------------------------------
# record_heartbeat / is_healthy
# ---------------------------------------------------------------------------

def test_is_healthy_unknown_pipeline_returns_none():
    assert hc.is_healthy("nonexistent") is None


def test_is_healthy_false_before_any_heartbeat():
    hc.register_healthcheck("pipe-a", tolerance_seconds=60)
    assert hc.is_healthy("pipe-a") is False


def test_is_healthy_true_after_recent_heartbeat(monkeypatch):
    hc.register_healthcheck("pipe-a", tolerance_seconds=60)
    monkeypatch.setattr(hc, "_now", lambda: 1_000_000.0)
    hc.record_heartbeat("pipe-a")
    assert hc.is_healthy("pipe-a") is True


def test_is_healthy_false_when_heartbeat_expired(monkeypatch):
    hc.register_healthcheck("pipe-a", tolerance_seconds=60)
    monkeypatch.setattr(hc, "_now", lambda: 1_000_000.0)
    hc.record_heartbeat("pipe-a")
    monkeypatch.setattr(hc, "_now", lambda: 1_000_000.0 + 61)
    assert hc.is_healthy("pipe-a") is False


def test_record_heartbeat_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        hc.record_heartbeat("  ")


# ---------------------------------------------------------------------------
# list_healthchecks / check_all
# ---------------------------------------------------------------------------

def test_list_healthchecks_returns_all_entries():
    hc.register_healthcheck("pipe-a")
    hc.register_healthcheck("pipe-b")
    names = {e["pipeline"] for e in hc.list_healthchecks()}
    assert names == {"pipe-a", "pipe-b"}


def test_check_all_includes_healthy_field(monkeypatch):
    hc.register_healthcheck("pipe-a", tolerance_seconds=300)
    monkeypatch.setattr(hc, "_now", lambda: 1_000_000.0)
    hc.record_heartbeat("pipe-a")
    results = hc.check_all()
    assert len(results) == 1
    assert results[0]["healthy"] is True
    assert results[0]["last_heartbeat"] == 1_000_000.0


def test_check_all_empty_when_no_registrations():
    assert hc.check_all() == []
