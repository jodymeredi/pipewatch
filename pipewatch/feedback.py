"""feedback.py – Pipeline alert feedback/resolution tracking.

Allows operators to mark alerts as resolved, false-positive, or
needs-investigation, providing a lightweight feedback loop for
improving alert quality over time.
"""
from __future__ import annotations

import datetime
from typing import Dict, List, Optional

_VALID_STATUSES = {"resolved", "false_positive", "needs_investigation"}

_registry: Dict[str, Dict] = {}


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def record_feedback(
    pipeline: str,
    status: str,
    note: str = "",
    author: str = "system",
) -> Dict:
    """Record operator feedback for a pipeline alert."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    status = status.strip().lower()
    if status not in _VALID_STATUSES:
        raise ValueError(
            f"status must be one of {sorted(_VALID_STATUSES)}, got {status!r}"
        )
    author = (author or "system").strip() or "system"
    entry = {
        "pipeline": pipeline,
        "status": status,
        "note": note.strip(),
        "author": author,
        "recorded_at": _utcnow().isoformat() + "Z",
    }
    _registry[pipeline] = entry
    return dict(entry)


def get_feedback(pipeline: str) -> Optional[Dict]:
    """Return current feedback entry for a pipeline, or None."""
    entry = _registry.get(pipeline.strip())
    return dict(entry) if entry else None


def clear_feedback(pipeline: str) -> bool:
    """Remove feedback entry for a pipeline. Returns True if removed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_feedback() -> List[Dict]:
    """Return all feedback entries sorted by pipeline name."""
    return [dict(v) for v in sorted(_registry.values(), key=lambda x: x["pipeline"])]


def pipelines_by_status(status: str) -> List[str]:
    """Return pipeline names that have a given feedback status."""
    status = status.strip().lower()
    return sorted(p for p, v in _registry.items() if v["status"] == status)
