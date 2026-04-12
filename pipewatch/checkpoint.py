"""Checkpoint tracking for pipeline stages.

Allows pipelines to register named checkpoints with timestamps so that
operators can detect stalled or missing stage completions.
"""

from __future__ import annotations

import time
from typing import Dict, List, Optional

_registry: Dict[str, Dict[str, float]] = {}


def _now() -> float:
    return time.time()


def record_checkpoint(pipeline: str, stage: str) -> dict:
    """Record that *stage* of *pipeline* completed right now."""
    if not pipeline or not pipeline.strip():
        raise ValueError("pipeline name must not be blank")
    if not stage or not stage.strip():
        raise ValueError("stage name must not be blank")
    _registry.setdefault(pipeline, {})[stage] = _now()
    return {"pipeline": pipeline, "stage": stage, "recorded_at": _registry[pipeline][stage]}


def get_checkpoint(pipeline: str, stage: str) -> Optional[float]:
    """Return the timestamp of the last completion, or None."""
    return _registry.get(pipeline, {}).get(stage)


def remove_checkpoint(pipeline: str, stage: str) -> bool:
    """Remove a single stage checkpoint.  Returns True if it existed."""
    stages = _registry.get(pipeline, {})
    if stage in stages:
        del stages[stage]
        if not stages:
            del _registry[pipeline]
        return True
    return False


def list_checkpoints(pipeline: str) -> List[dict]:
    """Return all recorded checkpoints for *pipeline*."""
    return [
        {"pipeline": pipeline, "stage": s, "recorded_at": ts}
        for s, ts in sorted(_registry.get(pipeline, {}).items())
    ]


def is_stale(pipeline: str, stage: str, max_age_seconds: float) -> bool:
    """Return True when the checkpoint exists but is older than *max_age_seconds*."""
    if max_age_seconds <= 0:
        raise ValueError("max_age_seconds must be positive")
    ts = get_checkpoint(pipeline, stage)
    if ts is None:
        return False
    return (_now() - ts) > max_age_seconds


def clear_pipeline(pipeline: str) -> int:
    """Remove all checkpoints for *pipeline*.  Returns the number removed."""
    stages = _registry.pop(pipeline, {})
    return len(stages)
