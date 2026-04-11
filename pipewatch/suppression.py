"""suppression.py – per-pipeline alert suppression rules based on metric status.

A suppression rule prevents alerts from being dispatched for a pipeline when
its current status matches a configured level (e.g. 'warning' only, not 'critical').
Unlike silencer.py (which uses time windows), suppression is level-based and
persists until explicitly removed.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional

# registry: pipeline_name -> {levels: set, created_at: float, reason: str}
_REGISTRY: Dict[str, dict] = {}

VALID_LEVELS = {"ok", "warning", "critical"}


def add_suppression(
    pipeline: str,
    levels: List[str],
    reason: str = "",
) -> dict:
    """Suppress alerts for *pipeline* when its status is in *levels*.

    Returns the stored rule dict.
    """
    invalid = set(levels) - VALID_LEVELS
    if invalid:
        raise ValueError(f"Invalid suppression levels: {invalid}")
    if not levels:
        raise ValueError("levels must contain at least one entry")

    rule = {
        "pipeline": pipeline,
        "levels": sorted(set(levels)),
        "reason": reason,
        "created_at": time.time(),
    }
    _REGISTRY[pipeline] = rule
    return rule


def remove_suppression(pipeline: str) -> bool:
    """Remove the suppression rule for *pipeline*.

    Returns True if a rule existed and was removed, False otherwise.
    """
    return _REGISTRY.pop(pipeline, None) is not None


def is_suppressed(pipeline: str, level: str) -> bool:
    """Return True if alerts for *pipeline* at *level* should be suppressed."""
    rule = _REGISTRY.get(pipeline)
    if rule is None:
        return False
    return level in rule["levels"]


def list_suppressions() -> List[dict]:
    """Return a copy of all active suppression rules."""
    return [dict(r) for r in _REGISTRY.values()]


def get_suppression(pipeline: str) -> Optional[dict]:
    """Return the suppression rule for *pipeline*, or None."""
    rule = _REGISTRY.get(pipeline)
    return dict(rule) if rule else None


def clear_all_suppressions() -> None:
    """Remove every suppression rule (primarily for testing)."""
    _REGISTRY.clear()
