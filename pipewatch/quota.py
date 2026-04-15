"""Pipeline alert quota management — cap total alerts per pipeline per window."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

_registry: Dict[str, dict] = {}
_counts: Dict[str, List[float]] = {}


def _now() -> float:
    return time.time()


def set_quota(pipeline: str, max_alerts: int, window_seconds: int = 3600) -> dict:
    """Register a quota for *pipeline*.

    Args:
        pipeline: Pipeline name.
        max_alerts: Maximum number of alerts allowed within the window.
        window_seconds: Rolling window length in seconds (default 1 hour).

    Returns:
        The stored quota rule as a dict.

    Raises:
        ValueError: If arguments are invalid.
    """
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if max_alerts < 1:
        raise ValueError("max_alerts must be >= 1")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be > 0")

    rule = {"pipeline": pipeline, "max_alerts": max_alerts, "window_seconds": window_seconds}
    _registry[pipeline] = rule
    return dict(rule)


def get_quota(pipeline: str) -> Optional[dict]:
    """Return the quota rule for *pipeline*, or None if not set."""
    rule = _registry.get(pipeline.strip())
    return dict(rule) if rule else None


def remove_quota(pipeline: str) -> bool:
    """Remove the quota rule for *pipeline*. Returns True if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_quotas() -> List[dict]:
    """Return all registered quota rules."""
    return [dict(r) for r in _registry.values()]


def is_quota_exceeded(pipeline: str) -> bool:
    """Return True if *pipeline* has exceeded its quota in the current window."""
    pipeline = pipeline.strip()
    rule = _registry.get(pipeline)
    if rule is None:
        return False
    window = rule["window_seconds"]
    cutoff = _now() - window
    timestamps = [t for t in _counts.get(pipeline, []) if t > cutoff]
    _counts[pipeline] = timestamps
    return len(timestamps) >= rule["max_alerts"]


def record_alert(pipeline: str) -> None:
    """Record that an alert was dispatched for *pipeline*."""
    pipeline = pipeline.strip()
    _counts.setdefault(pipeline, []).append(_now())


def remaining(pipeline: str) -> Optional[int]:
    """Return how many more alerts *pipeline* may send, or None if no quota set."""
    pipeline = pipeline.strip()
    rule = _registry.get(pipeline)
    if rule is None:
        return None
    window = rule["window_seconds"]
    cutoff = _now() - window
    active = [t for t in _counts.get(pipeline, []) if t > cutoff]
    _counts[pipeline] = active
    return max(0, rule["max_alerts"] - len(active))


def clear_counts(pipeline: str) -> None:
    """Reset the alert count for *pipeline* (useful for testing)."""
    _counts.pop(pipeline.strip(), None)
