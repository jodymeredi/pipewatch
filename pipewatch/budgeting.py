"""Alert budget tracking — limits total alerts fired per pipeline over a rolling window."""

from __future__ import annotations

import time
from typing import Dict, List, Optional

# {pipeline: {"max_alerts": int, "window_seconds": int, "fired": List[float]}}
_registry: Dict[str, dict] = {}


def _now() -> float:
    return time.time()


def set_budget(pipeline: str, max_alerts: int, window_seconds: int) -> dict:
    """Register or overwrite an alert budget for *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if max_alerts <= 0:
        raise ValueError("max_alerts must be a positive integer")
    if window_seconds <= 0:
        raise ValueError("window_seconds must be a positive integer")
    _registry[pipeline] = {
        "pipeline": pipeline,
        "max_alerts": max_alerts,
        "window_seconds": window_seconds,
        "fired": [],
    }
    return get_budget(pipeline)  # type: ignore[return-value]


def get_budget(pipeline: str) -> Optional[dict]:
    """Return a copy of the budget entry for *pipeline*, or None."""
    entry = _registry.get(pipeline.strip())
    if entry is None:
        return None
    return {
        "pipeline": entry["pipeline"],
        "max_alerts": entry["max_alerts"],
        "window_seconds": entry["window_seconds"],
    }


def remove_budget(pipeline: str) -> bool:
    """Remove the budget for *pipeline*. Returns True if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_budgets() -> List[dict]:
    """Return budget summaries for all registered pipelines."""
    return [get_budget(p) for p in _registry]  # type: ignore[misc]


def _purge_old_firings(entry: dict) -> None:
    cutoff = _now() - entry["window_seconds"]
    entry["fired"] = [t for t in entry["fired"] if t >= cutoff]


def is_over_budget(pipeline: str) -> bool:
    """Return True if *pipeline* has exhausted its alert budget."""
    entry = _registry.get(pipeline.strip())
    if entry is None:
        return False
    _purge_old_firings(entry)
    return len(entry["fired"]) >= entry["max_alerts"]


def record_alert(pipeline: str) -> None:
    """Record that an alert was fired for *pipeline*."""
    entry = _registry.get(pipeline.strip())
    if entry is None:
        return
    _purge_old_firings(entry)
    entry["fired"].append(_now())


def remaining(pipeline: str) -> Optional[int]:
    """Return how many alerts are still allowed in the current window, or None."""
    entry = _registry.get(pipeline.strip())
    if entry is None:
        return None
    _purge_old_firings(entry)
    return max(0, entry["max_alerts"] - len(entry["fired"]))


def reset_all() -> None:  # test helper
    _registry.clear()
