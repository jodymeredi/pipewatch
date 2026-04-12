"""Pipeline alert priority management.

Allows assigning numeric priority levels to pipelines so that dispatch
and reporting can order or filter alerts accordingly.
"""

from __future__ import annotations

from typing import Dict, List, Optional

_registry: Dict[str, int] = {}

_DEFAULT_PRIORITY = 50  # mid-range default (1 = highest, 100 = lowest)


def set_priority(pipeline: str, level: int) -> dict:
    """Assign a numeric priority level to *pipeline*.

    Args:
        pipeline: Non-blank pipeline name.
        level: Integer in the range [1, 100].

    Returns:
        Dict with ``pipeline`` and ``priority`` keys.

    Raises:
        ValueError: If *pipeline* is blank or *level* is out of range.
    """
    if not pipeline or not pipeline.strip():
        raise ValueError("pipeline must be a non-blank string")
    if not (1 <= level <= 100):
        raise ValueError("priority level must be between 1 and 100 inclusive")
    _registry[pipeline.strip()] = level
    return {"pipeline": pipeline.strip(), "priority": level}


def get_priority(pipeline: str) -> int:
    """Return the priority for *pipeline*, or the default if unset."""
    return _registry.get(pipeline.strip(), _DEFAULT_PRIORITY)


def remove_priority(pipeline: str) -> bool:
    """Remove the explicit priority for *pipeline*.

    Returns True if an entry was removed, False if none existed.
    """
    return _registry.pop(pipeline.strip(), None) is not None


def list_priorities() -> List[dict]:
    """Return all explicitly configured priorities sorted by level (ascending)."""
    return [
        {"pipeline": p, "priority": lvl}
        for p, lvl in sorted(_registry.items(), key=lambda x: x[1])
    ]


def sort_by_priority(pipelines: List[str]) -> List[str]:
    """Return *pipelines* sorted from highest (1) to lowest (100) priority."""
    return sorted(pipelines, key=lambda p: get_priority(p))


def clear_priorities() -> None:  # noqa: D401 – test helper
    """Remove all priority entries (primarily for testing)."""
    _registry.clear()
