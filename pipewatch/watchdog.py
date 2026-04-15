"""Watchdog: detect pipelines that have stopped reporting metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from pipewatch.history import load_snapshots

_registry: Dict[str, Dict] = {}  # pipeline -> {max_silence_seconds, label}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def set_watchdog(pipeline: str, max_silence_seconds: int, label: str = "") -> Dict:
    """Register a watchdog for a pipeline.

    Args:
        pipeline: Pipeline name.
        max_silence_seconds: Seconds without a snapshot before the pipeline is
            considered stale.
        label: Optional human-readable label.

    Returns:
        The registered watchdog rule as a dict.
    """
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if max_silence_seconds <= 0:
        raise ValueError("max_silence_seconds must be a positive integer")

    rule = {
        "pipeline": pipeline,
        "max_silence_seconds": max_silence_seconds,
        "label": label.strip(),
    }
    _registry[pipeline] = rule
    return dict(rule)


def remove_watchdog(pipeline: str) -> bool:
    """Remove a watchdog rule.  Returns True if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def get_watchdog(pipeline: str) -> Optional[Dict]:
    """Return the watchdog rule for *pipeline*, or None."""
    rule = _registry.get(pipeline.strip())
    return dict(rule) if rule else None


def list_watchdogs() -> List[Dict]:
    """Return all registered watchdog rules."""
    return [dict(r) for r in _registry.values()]


def check_watchdogs(history_dir: Optional[str] = None) -> List[Dict]:
    """Evaluate all watchdog rules against recorded history.

    Returns a list of result dicts, one per registered pipeline, with keys:
        pipeline, stale (bool), last_seen (ISO str or None), elapsed_seconds.
    """
    now = _utcnow()
    results: List[Dict] = []

    for pipeline, rule in _registry.items():
        snapshots = load_snapshots(history_dir) if history_dir else load_snapshots()
        last_seen: Optional[datetime] = None

        for snap in snapshots:
            for metric in snap.get("metrics", []):
                if metric.get("pipeline") == pipeline:
                    ts_str = snap.get("recorded_at") or snap.get("timestamp")
                    if ts_str:
                        try:
                            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                            if ts.tzinfo is None:
                                ts = ts.replace(tzinfo=timezone.utc)
                            if last_seen is None or ts > last_seen:
                                last_seen = ts
                        except ValueError:
                            pass

        elapsed = (now - last_seen).total_seconds() if last_seen else None
        stale = elapsed is None or elapsed > rule["max_silence_seconds"]

        results.append({
            "pipeline": pipeline,
            "stale": stale,
            "last_seen": last_seen.isoformat() if last_seen else None,
            "elapsed_seconds": elapsed,
            "max_silence_seconds": rule["max_silence_seconds"],
        })

    return results
