"""Alert throttling: suppress repeated alerts for the same pipeline within a cooldown window."""

from __future__ import annotations

import time
from typing import Dict, Optional, Tuple

# Registry: pipeline_name -> (last_alert_epoch, cooldown_seconds)
_throttle_registry: Dict[str, Tuple[float, float]] = {}

_DEFAULT_COOLDOWN = 300.0  # 5 minutes


def _now() -> float:
    """Return current epoch time. Isolated for testing."""
    return time.time()


def set_cooldown(pipeline: str, cooldown_seconds: float = _DEFAULT_COOLDOWN) -> None:
    """Register or update the cooldown period for a pipeline.

    Resets the last-alert timestamp so the next alert fires immediately.
    """
    if cooldown_seconds < 0:
        raise ValueError("cooldown_seconds must be non-negative")
    _throttle_registry[pipeline] = (0.0, cooldown_seconds)


def is_throttled(pipeline: str) -> bool:
    """Return True if the pipeline is within its cooldown window."""
    if pipeline not in _throttle_registry:
        return False
    last_alert, cooldown = _throttle_registry[pipeline]
    return (_now() - last_alert) < cooldown


def record_alert(pipeline: str, cooldown_seconds: Optional[float] = None) -> None:
    """Mark that an alert was just fired for *pipeline*.

    If the pipeline has no existing entry a default cooldown is applied unless
    *cooldown_seconds* is provided explicitly.
    """
    if cooldown_seconds is not None and cooldown_seconds < 0:
        raise ValueError("cooldown_seconds must be non-negative")
    if pipeline in _throttle_registry:
        _, existing_cooldown = _throttle_registry[pipeline]
        effective_cooldown = cooldown_seconds if cooldown_seconds is not None else existing_cooldown
    else:
        effective_cooldown = cooldown_seconds if cooldown_seconds is not None else _DEFAULT_COOLDOWN
    _throttle_registry[pipeline] = (_now(), effective_cooldown)


def clear_throttle(pipeline: str) -> bool:
    """Remove the throttle entry for *pipeline*. Returns True if it existed."""
    return _throttle_registry.pop(pipeline, None) is not None


def list_throttles() -> Dict[str, Dict[str, float]]:
    """Return a snapshot of all active throttle entries."""
    now = _now()
    result = {}
    for pipeline, (last_alert, cooldown) in _throttle_registry.items():
        elapsed = now - last_alert
        remaining = max(0.0, cooldown - elapsed)
        result[pipeline] = {
            "last_alert_epoch": last_alert,
            "cooldown_seconds": cooldown,
            "remaining_seconds": remaining,
            "throttled": elapsed < cooldown,
        }
    return result


def reset_all() -> None:
    """Clear the entire throttle registry. Intended for tests."""
    _throttle_registry.clear()
