"""Circuit breaker for pipeline alert dispatching.

Tracks consecutive failures per pipeline and opens the circuit
(halts dispatching) once a threshold is exceeded. The circuit
automatically moves to half-open after a cooldown period.
"""

from __future__ import annotations

import time
from typing import Dict, Any, Optional

# States
CLOSED = "closed"       # normal operation
OPEN = "open"           # failures exceeded threshold; dispatching halted
HALF_OPEN = "half_open" # cooldown elapsed; next dispatch is a probe

_DEFAULT_THRESHOLD = 3      # consecutive failures before opening
_DEFAULT_COOLDOWN = 60.0    # seconds before transitioning to half-open

_registry: Dict[str, Dict[str, Any]] = {}


def _now() -> float:
    return time.monotonic()


def register_breaker(
    pipeline: str,
    threshold: int = _DEFAULT_THRESHOLD,
    cooldown: float = _DEFAULT_COOLDOWN,
) -> Dict[str, Any]:
    """Register or overwrite a circuit breaker for *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if threshold < 1:
        raise ValueError("threshold must be >= 1")
    if cooldown <= 0:
        raise ValueError("cooldown must be > 0")
    _registry[pipeline] = {
        "pipeline": pipeline,
        "threshold": threshold,
        "cooldown": cooldown,
        "failures": 0,
        "state": CLOSED,
        "opened_at": None,
    }
    return dict(_registry[pipeline])


def remove_breaker(pipeline: str) -> bool:
    return _registry.pop(pipeline.strip(), None) is not None


def get_state(pipeline: str) -> Optional[str]:
    """Return current state or None if no breaker is registered."""
    entry = _registry.get(pipeline.strip())
    if entry is None:
        return None
    if entry["state"] == OPEN:
        elapsed = _now() - entry["opened_at"]
        if elapsed >= entry["cooldown"]:
            entry["state"] = HALF_OPEN
    return entry["state"]


def record_failure(pipeline: str) -> str:
    """Record a dispatch failure; returns the new state."""
    pipeline = pipeline.strip()
    if pipeline not in _registry:
        register_breaker(pipeline)
    entry = _registry[pipeline]
    entry["failures"] += 1
    if entry["failures"] >= entry["threshold"] and entry["state"] != OPEN:
        entry["state"] = OPEN
        entry["opened_at"] = _now()
    return entry["state"]


def record_success(pipeline: str) -> str:
    """Record a successful dispatch; resets the breaker. Returns new state."""
    pipeline = pipeline.strip()
    if pipeline not in _registry:
        return CLOSED
    entry = _registry[pipeline]
    entry["failures"] = 0
    entry["state"] = CLOSED
    entry["opened_at"] = None
    return CLOSED


def list_breakers() -> list:
    return [dict(e) for e in _registry.values()]
