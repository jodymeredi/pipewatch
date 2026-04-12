"""Alert deduplication: suppress repeated alerts for the same pipeline+level
within a configurable time window."""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

# Registry: (pipeline, level) -> last_alert_epoch
_registry: Dict[Tuple[str, str], float] = {}

# Default dedup window in seconds
_DEFAULT_WINDOW_SECONDS = 300  # 5 minutes
_windows: Dict[Tuple[str, str], float] = {}


def _now() -> float:
    return time.time()


def set_window(pipeline: str, level: str, seconds: float) -> None:
    """Set a custom deduplication window for a pipeline+level pair."""
    if seconds < 0:
        raise ValueError("Deduplication window must be non-negative.")
    _windows[(pipeline, level)] = seconds


def _get_window(pipeline: str, level: str) -> float:
    return _windows.get((pipeline, level), _DEFAULT_WINDOW_SECONDS)


def is_duplicate(pipeline: str, level: str) -> bool:
    """Return True if an alert for this pipeline+level was already dispatched
    within the deduplication window."""
    key = (pipeline, level)
    last = _registry.get(key)
    if last is None:
        return False
    return (_now() - last) < _get_window(pipeline, level)


def record_alert(pipeline: str, level: str) -> None:
    """Record that an alert was dispatched for pipeline+level right now."""
    _registry[(pipeline, level)] = _now()


def clear(pipeline: str, level: Optional[str] = None) -> None:
    """Clear deduplication state for a pipeline, optionally scoped to a level."""
    if level is not None:
        _registry.pop((pipeline, level), None)
    else:
        keys = [k for k in _registry if k[0] == pipeline]
        for k in keys:
            del _registry[k]


def list_entries() -> list:
    """Return current deduplication entries as a list of dicts."""
    now = _now()
    return [
        {
            "pipeline": pipeline,
            "level": level,
            "last_alert_ago_seconds": round(now - ts, 3),
            "window_seconds": _get_window(pipeline, level),
        }
        for (pipeline, level), ts in sorted(_registry.items())
    ]
