"""scheduling.py – simple cron-style run schedule registry for pipelines.

Allows operators to register expected run intervals per pipeline and check
whether a pipeline is overdue based on history snapshots.
"""

from __future__ import annotations

import datetime
from typing import Dict, List, Optional

# {pipeline: interval_seconds}
_schedules: Dict[str, int] = {}


def _utcnow() -> datetime.datetime:
    return datetime.datetime.utcnow()


def set_schedule(pipeline: str, interval_seconds: int) -> dict:
    """Register or update the expected run interval for *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be a positive integer")
    _schedules[pipeline] = interval_seconds
    return {"pipeline": pipeline, "interval_seconds": interval_seconds}


def get_schedule(pipeline: str) -> Optional[int]:
    """Return the registered interval (seconds) for *pipeline*, or None."""
    return _schedules.get(pipeline)


def remove_schedule(pipeline: str) -> bool:
    """Remove the schedule for *pipeline*. Returns True if it existed."""
    if pipeline in _schedules:
        del _schedules[pipeline]
        return True
    return False


def list_schedules() -> List[dict]:
    """Return a list of all registered schedules as dicts."""
    return [
        {"pipeline": p, "interval_seconds": s}
        for p, s in sorted(_schedules.items())
    ]


def is_overdue(pipeline: str, last_run_at: Optional[datetime.datetime]) -> bool:
    """Return True if *pipeline* has exceeded its registered interval.

    If no schedule is registered or *last_run_at* is None the pipeline is
    considered overdue only when there is a registered schedule and no run
    timestamp is available.
    """
    interval = _schedules.get(pipeline)
    if interval is None:
        return False
    if last_run_at is None:
        return True
    elapsed = (_utcnow() - last_run_at).total_seconds()
    return elapsed > interval


def overdue_pipelines(
    last_runs: Dict[str, Optional[datetime.datetime]]
) -> List[str]:
    """Return names of all scheduled pipelines that are currently overdue."""
    return [
        pipeline
        for pipeline in _schedules
        if is_overdue(pipeline, last_runs.get(pipeline))
    ]
