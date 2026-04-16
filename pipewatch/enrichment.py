"""Metric enrichment — attach contextual metadata to pipeline metrics before dispatch."""

from __future__ import annotations

from typing import Any

_registry: dict[str, dict[str, Any]] = {}


def set_enrichment(pipeline: str, **fields: Any) -> dict[str, Any]:
    """Register arbitrary enrichment fields for a pipeline."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if not fields:
        raise ValueError("at least one enrichment field is required")
    _registry[pipeline] = dict(fields)
    return {"pipeline": pipeline, "fields": _registry[pipeline]}


def get_enrichment(pipeline: str) -> dict[str, Any]:
    """Return enrichment fields for *pipeline*, or an empty dict."""
    return dict(_registry.get(pipeline.strip(), {}))


def remove_enrichment(pipeline: str) -> bool:
    """Remove enrichment for *pipeline*. Returns True if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_enrichments() -> list[dict[str, Any]]:
    """Return all registered enrichment entries."""
    return [{"pipeline": p, "fields": dict(f)} for p, f in _registry.items()]


def enrich_metric(metric: Any) -> dict[str, Any]:
    """Return metric as dict with enrichment fields merged in (non-destructive).

    Enrichment fields are added under the key ``enrichment`` so they never
    overwrite core metric attributes.
    """
    from pipewatch.metrics import as_dict  # local import to avoid circularity

    base = as_dict(metric) if not isinstance(metric, dict) else dict(metric)
    extra = get_enrichment(base.get("pipeline", ""))
    base["enrichment"] = extra
    return base


def enrich_bulk(metrics: list[Any]) -> list[dict[str, Any]]:
    """Enrich a list of metrics, returning a list of enriched dicts."""
    return [enrich_metric(m) for m in metrics]
