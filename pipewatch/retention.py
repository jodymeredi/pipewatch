"""Retention policy management for pipeline snapshot history."""
from __future__ import annotations

import datetime
from typing import Dict, Optional

_registry: Dict[str, Dict] = {}
_default_policy: Dict = {"max_days": 30, "max_snapshots": 500}


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def set_policy(pipeline: str, max_days: Optional[int] = None, max_snapshots: Optional[int] = None) -> Dict:
    """Set a retention policy for a pipeline."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if max_days is not None and max_days <= 0:
        raise ValueError("max_days must be a positive integer")
    if max_snapshots is not None and max_snapshots <= 0:
        raise ValueError("max_snapshots must be a positive integer")

    policy = {
        "pipeline": pipeline,
        "max_days": max_days,
        "max_snapshots": max_snapshots,
    }
    _registry[pipeline] = policy
    return dict(policy)


def get_policy(pipeline: str) -> Optional[Dict]:
    """Return the retention policy for a pipeline, or None if not set."""
    entry = _registry.get(pipeline)
    return dict(entry) if entry else None


def remove_policy(pipeline: str) -> bool:
    """Remove a retention policy. Returns True if it existed."""
    return _registry.pop(pipeline, None) is not None


def list_policies() -> list:
    """Return all registered retention policies."""
    return [dict(v) for v in _registry.values()]


def set_default_policy(max_days: int = 30, max_snapshots: int = 500) -> Dict:
    """Set the global default retention policy."""
    if max_days <= 0:
        raise ValueError("max_days must be positive")
    if max_snapshots <= 0:
        raise ValueError("max_snapshots must be positive")
    _default_policy["max_days"] = max_days
    _default_policy["max_snapshots"] = max_snapshots
    return dict(_default_policy)


def resolve_policy(pipeline: str) -> Dict:
    """Return the effective policy for a pipeline (specific or default)."""
    return dict(_registry.get(pipeline, _default_policy))


def apply_retention(pipeline: str, snapshots: list) -> list:
    """Filter snapshots according to the resolved retention policy.

    *snapshots* is a list of dicts each containing a ``recorded_at`` ISO
    timestamp string.  Returns the snapshots that should be kept.
    """
    policy = resolve_policy(pipeline)
    now = _utcnow()
    kept = list(snapshots)

    max_days = policy.get("max_days")
    if max_days:
        cutoff = now - datetime.timedelta(days=max_days)
        kept = [
            s for s in kept
            if datetime.datetime.fromisoformat(s["recorded_at"]) >= cutoff
        ]

    max_snapshots = policy.get("max_snapshots")
    if max_snapshots and len(kept) > max_snapshots:
        kept = kept[-max_snapshots:]

    return kept
