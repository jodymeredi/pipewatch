"""Alert fingerprinting — generates stable identifiers for alert events
so that downstream systems can deduplicate, correlate, and track
recurring alert patterns across runs."""

from __future__ import annotations

import hashlib
import json
from typing import Any

_registry: dict[str, dict[str, Any]] = {}


def _make_fingerprint(pipeline: str, level: str, metric_name: str) -> str:
    """Return a stable hex fingerprint for the given alert dimensions."""
    payload = json.dumps(
        {"pipeline": pipeline.strip(), "level": level.lower(), "metric": metric_name.strip()},
        sort_keys=True,
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def register_fingerprint(pipeline: str, level: str, metric_name: str) -> dict[str, Any]:
    """Compute and store a fingerprint for the alert triple; return the record."""
    pipeline = pipeline.strip()
    level = level.strip().lower()
    metric_name = metric_name.strip()

    if not pipeline:
        raise ValueError("pipeline must not be blank")
    if not level:
        raise ValueError("level must not be blank")
    if not metric_name:
        raise ValueError("metric_name must not be blank")

    fp = _make_fingerprint(pipeline, level, metric_name)
    record: dict[str, Any] = {
        "fingerprint": fp,
        "pipeline": pipeline,
        "level": level,
        "metric_name": metric_name,
        "hit_count": _registry.get(fp, {}).get("hit_count", 0) + 1,
    }
    _registry[fp] = record
    return dict(record)


def get_fingerprint(pipeline: str, level: str, metric_name: str) -> dict[str, Any] | None:
    """Return the stored record for the fingerprint triple, or None."""
    fp = _make_fingerprint(pipeline, level, metric_name)
    record = _registry.get(fp)
    return dict(record) if record else None


def remove_fingerprint(pipeline: str, level: str, metric_name: str) -> bool:
    """Remove a fingerprint record; return True if it existed."""
    fp = _make_fingerprint(pipeline, level, metric_name)
    if fp in _registry:
        del _registry[fp]
        return True
    return False


def list_fingerprints() -> list[dict[str, Any]]:
    """Return all registered fingerprint records."""
    return [dict(v) for v in _registry.values()]


def reset_registry() -> None:  # test helper
    _registry.clear()
