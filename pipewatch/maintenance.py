"""Maintenance window management for pipewatch.

Allows pipelines to be placed in a maintenance window during which
alerts are suppressed and status checks are skipped.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

_registry: Dict[str, dict] = {}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def add_window(
    pipeline: str,
    starts_at: datetime,
    ends_at: datetime,
    reason: str = "",
    created_by: str = "system",
) -> dict:
    """Register a maintenance window for *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if ends_at <= starts_at:
        raise ValueError("ends_at must be after starts_at")

    window_id = str(uuid.uuid4())
    entry = {
        "id": window_id,
        "pipeline": pipeline,
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "reason": reason.strip(),
        "created_by": created_by.strip() or "system",
    }
    _registry[window_id] = entry
    return dict(entry)


def remove_window(window_id: str) -> bool:
    """Remove a maintenance window by ID. Returns True if removed."""
    if window_id in _registry:
        del _registry[window_id]
        return True
    return False


def is_in_maintenance(pipeline: str, at: Optional[datetime] = None) -> bool:
    """Return True if *pipeline* has an active maintenance window at *at*."""
    now = at or _utcnow()
    for entry in _registry.values():
        if entry["pipeline"] != pipeline:
            continue
        starts = datetime.fromisoformat(entry["starts_at"])
        ends = datetime.fromisoformat(entry["ends_at"])
        if starts <= now <= ends:
            return True
    return False


def list_windows(pipeline: Optional[str] = None) -> List[dict]:
    """Return all maintenance windows, optionally filtered by pipeline."""
    windows = list(_registry.values())
    if pipeline is not None:
        windows = [w for w in windows if w["pipeline"] == pipeline]
    return [dict(w) for w in windows]


def purge_expired(at: Optional[datetime] = None) -> int:
    """Remove all expired maintenance windows. Returns count removed."""
    now = at or _utcnow()
    expired = [
        wid
        for wid, entry in _registry.items()
        if datetime.fromisoformat(entry["ends_at"]) < now
    ]
    for wid in expired:
        del _registry[wid]
    return len(expired)
