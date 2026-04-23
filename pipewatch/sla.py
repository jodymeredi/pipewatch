"""SLA tracking for pipelines — record expected completion windows and detect violations."""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional

_registry: Dict[str, dict] = {}


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def set_sla(
    pipeline: str,
    deadline_utc: str,
    window_minutes: int = 60,
    description: str = "",
) -> dict:
    """Register or overwrite an SLA rule for a pipeline.

    Args:
        pipeline: Pipeline name.
        deadline_utc: Daily deadline as "HH:MM" (UTC).
        window_minutes: Grace window in minutes after the deadline.
        description: Optional human-readable description.
    """
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    try:
        hour, minute = [int(p) for p in deadline_utc.strip().split(":")]
    except Exception:
        raise ValueError("deadline_utc must be in HH:MM format")
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError("deadline_utc hour/minute out of range")
    if window_minutes < 0:
        raise ValueError("window_minutes must be >= 0")

    rule = {
        "pipeline": pipeline,
        "deadline_utc": f"{hour:02d}:{minute:02d}",
        "window_minutes": window_minutes,
        "description": description.strip(),
    }
    _registry[pipeline] = rule
    return dict(rule)


def get_sla(pipeline: str) -> Optional[dict]:
    entry = _registry.get(pipeline.strip())
    return dict(entry) if entry else None


def remove_sla(pipeline: str) -> bool:
    return _registry.pop(pipeline.strip(), None) is not None


def list_slas() -> List[dict]:
    return [dict(v) for v in _registry.values()]


def check_sla(pipeline: str, last_run_utc: Optional[datetime.datetime] = None) -> dict:
    """Check whether the pipeline has met its SLA.

    Returns a dict with keys: pipeline, status ('ok'|'breached'|'unknown'), message.
    """
    rule = _registry.get(pipeline.strip())
    if rule is None:
        return {"pipeline": pipeline, "status": "unknown", "message": "no SLA registered"}

    now = _utcnow()
    hour, minute = [int(p) for p in rule["deadline_utc"].split(":")]
    deadline_today = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    cutoff = deadline_today + datetime.timedelta(minutes=rule["window_minutes"])

    if now < deadline_today:
        return {"pipeline": pipeline, "status": "ok", "message": "deadline not yet reached"}

    if last_run_utc is not None and last_run_utc >= deadline_today:
        return {"pipeline": pipeline, "status": "ok", "message": "completed within SLA"}

    if now > cutoff:
        return {
            "pipeline": pipeline,
            "status": "breached",
            "message": f"SLA breached — deadline was {rule['deadline_utc']} UTC",
        }

    return {
        "pipeline": pipeline,
        "status": "breached",
        "message": f"past deadline {rule['deadline_utc']} UTC, within grace window",
    }
