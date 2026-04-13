"""Acknowledgment module: track manual acknowledgment of pipeline alerts."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

_registry: Dict[str, dict] = {}  # key: pipeline


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def acknowledge(
    pipeline: str,
    level: str,
    acknowledged_by: str,
    note: str = "",
    expires_at: Optional[datetime] = None,
) -> dict:
    """Acknowledge an alert for a pipeline at the given severity level."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    acknowledged_by = acknowledged_by.strip()
    if not acknowledged_by:
        raise ValueError("acknowledged_by must not be blank")
    valid_levels = {"ok", "warning", "critical"}
    level = level.lower().strip()
    if level not in valid_levels:
        raise ValueError(f"level must be one of {valid_levels}")

    entry = {
        "id": str(uuid.uuid4()),
        "pipeline": pipeline,
        "level": level,
        "acknowledged_by": acknowledged_by,
        "note": note.strip(),
        "acknowledged_at": _utcnow().isoformat(),
        "expires_at": expires_at.isoformat() if expires_at else None,
    }
    _registry[pipeline] = entry
    return entry


def is_acknowledged(pipeline: str, level: str) -> bool:
    """Return True if the pipeline has an active acknowledgment for the level."""
    entry = _registry.get(pipeline)
    if not entry:
        return False
    if entry["level"] != level.lower().strip():
        return False
    if entry["expires_at"] is not None:
        exp = datetime.fromisoformat(entry["expires_at"])
        if _utcnow() > exp:
            del _registry[pipeline]
            return False
    return True


def clear_acknowledgment(pipeline: str) -> bool:
    """Remove acknowledgment for a pipeline. Returns True if one existed."""
    if pipeline in _registry:
        del _registry[pipeline]
        return True
    return False


def get_acknowledgment(pipeline: str) -> Optional[dict]:
    """Return the acknowledgment entry for a pipeline, or None."""
    return dict(_registry[pipeline]) if pipeline in _registry else None


def list_acknowledgments() -> List[dict]:
    """Return all current acknowledgment entries."""
    return [dict(v) for v in _registry.values()]
