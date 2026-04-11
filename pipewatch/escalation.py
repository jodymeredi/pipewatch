"""Escalation policy: re-alert when a pipeline stays in a breached state
for longer than a configured escalation window."""

from __future__ import annotations

import time
from typing import Dict, Optional

# Registry: pipeline_name -> {"first_breach_at": float, "level": str}
_breach_registry: Dict[str, Dict] = {}

# Default escalation window in seconds (5 minutes)
DEFAULT_ESCALATION_WINDOW: int = 300


def _now() -> float:  # pragma: no cover – thin wrapper for testability
    return time.time()


def record_breach(pipeline: str, level: str, *, _ts: Optional[float] = None) -> None:
    """Record or update a breach for *pipeline* at severity *level*.

    If the pipeline is already breached at the same level the first_breach_at
    timestamp is preserved so the escalation window is measured from the
    original breach.
    """
    ts = _ts if _ts is not None else _now()
    existing = _breach_registry.get(pipeline)
    if existing and existing["level"] == level:
        # Keep original timestamp – do not reset the clock.
        return
    _breach_registry[pipeline] = {"first_breach_at": ts, "level": level}


def clear_breach(pipeline: str) -> None:
    """Remove a pipeline from the breach registry (metric recovered)."""
    _breach_registry.pop(pipeline, None)


def should_escalate(
    pipeline: str,
    window: int = DEFAULT_ESCALATION_WINDOW,
    *,
    _ts: Optional[float] = None,
) -> bool:
    """Return True when *pipeline* has been continuously breached for at
    least *window* seconds and therefore warrants a re-alert.
    """
    entry = _breach_registry.get(pipeline)
    if entry is None:
        return False
    ts = _ts if _ts is not None else _now()
    return (ts - entry["first_breach_at"]) >= window


def list_breaches() -> Dict[str, Dict]:
    """Return a shallow copy of the current breach registry."""
    return dict(_breach_registry)


def reset_registry() -> None:  # test helper
    """Clear all breach state – intended for use in tests only."""
    _breach_registry.clear()
