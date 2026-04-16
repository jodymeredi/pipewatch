"""Tests for pipewatch.enrichment."""

from __future__ import annotations

import pytest

import pipewatch.enrichment as enrichment
from pipewatch.metrics import collect_metric


@pytest.fixture(autouse=True)
def reset_registry():
    enrichment._registry.clear()
    yield
    enrichment._registry.clear()


def _make_metric(pipeline="pipe-a", value=10.0, status="ok"):
    return collect_metric(pipeline, value, status=status)


def test_set_enrichment_returns_dict():
    result = enrichment.set_enrichment("pipe-a", env="prod", team="data")
    assert result["pipeline"] == "pipe-a"
    assert result["fields"] == {"env": "prod", "team": "data"}


def test_set_enrichment_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        enrichment.set_enrichment("  ", env="prod")


def test_set_enrichment_no_fields_raises():
    with pytest.raises(ValueError, match="at least one"):
        enrichment.set_enrichment("pipe-a")


def test_get_enrichment_returns_fields():
    enrichment.set_enrichment("pipe-a", env="staging")
    assert enrichment.get_enrichment("pipe-a") == {"env": "staging"}


def test_get_enrichment_returns_empty_for_unknown():
    assert enrichment.get_enrichment("unknown") == {}


def test_remove_enrichment_returns_true_when_present():
    enrichment.set_enrichment("pipe-a", env="prod")
    assert enrichment.remove_enrichment("pipe-a") is True
    assert enrichment.get_enrichment("pipe-a") == {}


def test_remove_enrichment_returns_false_when_absent():
    assert enrichment.remove_enrichment("nonexistent") is False


def test_list_enrichments_reflects_registered():
    enrichment.set_enrichment("pipe-a", env="prod")
    enrichment.set_enrichment("pipe-b", env="dev", owner="alice")
    entries = enrichment.list_enrichments()
    pipelines = {e["pipeline"] for e in entries}
    assert pipelines == {"pipe-a", "pipe-b"}


def test_enrich_metric_adds_enrichment_key():
    enrichment.set_enrichment("pipe-a", env="prod")
    m = _make_metric("pipe-a")
    result = enrichment.enrich_metric(m)
    assert "enrichment" in result
    assert result["enrichment"]["env"] == "prod"


def test_enrich_metric_empty_when_no_registration():
    m = _make_metric("pipe-z")
    result = enrichment.enrich_metric(m)
    assert result["enrichment"] == {}


def test_enrich_bulk_processes_all_metrics():
    enrichment.set_enrichment("pipe-a", region="us-east")
    metrics = [_make_metric("pipe-a"), _make_metric("pipe-b")]
    results = enrichment.enrich_bulk(metrics)
    assert len(results) == 2
    assert results[0]["enrichment"] == {"region": "us-east"}
    assert results[1]["enrichment"] == {}


def test_overwrite_enrichment_updates_fields():
    enrichment.set_enrichment("pipe-a", env="prod")
    enrichment.set_enrichment("pipe-a", env="staging", team="ops")
    fields = enrichment.get_enrichment("pipe-a")
    assert fields == {"env": "staging", "team": "ops"}
