"""Pipeline health-check registry.

Allows callers to register expected liveness signals for a pipeline and
query whether it is currently considered healthy (i.e. a heartbeat was
received within the configured tolerance window).
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

_registry: Dict[str, dict] = {}
_heartbeats: Dict[str, float] = {}


def _now() -> float:  # pragma: no cover — thin wrapper kept for test patching
    return time.time()


def register_healthcheck(
    pipeline: str,
    tolerance_seconds: int = 300,
    label: str = "",
) -> dict:
    """Register (or overwrite) a health-check entry for *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if tolerance_seconds <= 0:
        raise ValueError("tolerance_seconds must be positive")

    entry = {
        "pipeline": pipeline,
        "tolerance_seconds": tolerance_seconds,
        "label": label.strip(),
    }
    _registry[pipeline] = entry
    return dict(entry)


def remove_healthcheck(pipeline: str) -> bool:
    """Remove a health-check registration.  Returns True if it existed."""
    pipeline = pipeline.strip()
    _registry.pop(pipeline, None)
    _heartbeats.pop(pipeline, None)
    return True


def record_heartbeat(pipeline: str) -> float:
    """Record that *pipeline* is alive right now.  Returns the timestamp."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    ts = _now()
    _heartbeats[pipeline] = ts
    return ts


def is_healthy(pipeline: str) -> Optional[bool]:
    """Return True/False if registered, None if unknown."""
    pipeline = pipeline.strip()
    if pipeline not in _registry:
        return None
    last = _heartbeats.get(pipeline)
    if last is None:
        return False
    tolerance = _registry[pipeline]["tolerance_seconds"]
    return (_now() - last) <= tolerance


def get_healthcheck(pipeline: str) -> Optional[dict]:
    """Return the registered entry or None."""
    return dict(_registry[pipeline]) if pipeline.strip() in _registry else None


def list_healthchecks() -> List[dict]:
    """Return all registered health-check entries."""
    return [dict(v) for v in _registry.values()]


def check_all() -> List[dict]:
    """Evaluate every registered pipeline and return a status list."""
    results = []
    for name, entry in _registry.items():
        last = _heartbeats.get(name)
        healthy = is_healthy(name)
        results.append(
            {
                "pipeline": name,
                "healthy": healthy,
                "last_heartbeat": last,
                "tolerance_seconds": entry["tolerance_seconds"],
                "label": entry["label"],
            }
        )
    return results
