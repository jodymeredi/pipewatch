"""Baseline management: store and compare expected metric values per pipeline."""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

_BASELINES: Dict[str, Dict] = {}


def _baseline_path(directory: str) -> str:
    return os.path.join(directory, "baselines.json")


def load_baselines(directory: str) -> None:
    """Load baselines from a JSON file into the in-memory registry."""
    global _BASELINES
    path = _baseline_path(directory)
    if not os.path.exists(path):
        _BASELINES = {}
        return
    with open(path, "r") as fh:
        _BASELINES = json.load(fh)


def save_baselines(directory: str) -> None:
    """Persist the current in-memory registry to disk."""
    os.makedirs(directory, exist_ok=True)
    with open(_baseline_path(directory), "w") as fh:
        json.dump(_BASELINES, fh, indent=2)


def set_baseline(pipeline: str, metric_name: str, value: float) -> Dict:
    """Record an expected baseline value for a pipeline metric."""
    _BASELINES.setdefault(pipeline, {})
    _BASELINES[pipeline][metric_name] = value
    return {"pipeline": pipeline, "metric": metric_name, "baseline": value}


def get_baseline(pipeline: str, metric_name: str) -> Optional[float]:
    """Return the stored baseline value, or None if not set."""
    return _BASELINES.get(pipeline, {}).get(metric_name)


def remove_baseline(pipeline: str, metric_name: str) -> bool:
    """Remove a baseline entry. Returns True if it existed."""
    if pipeline in _BASELINES and metric_name in _BASELINES[pipeline]:
        del _BASELINES[pipeline][metric_name]
        if not _BASELINES[pipeline]:
            del _BASELINES[pipeline]
        return True
    return False


def compare_to_baseline(
    pipeline: str, metric_name: str, current: float, tolerance: float = 0.1
) -> Optional[Dict]:
    """Compare *current* against the stored baseline.

    Returns a dict with deviation info, or None if no baseline is set.
    *tolerance* is a fractional threshold (0.1 == 10%).
    """
    baseline = get_baseline(pipeline, metric_name)
    if baseline is None:
        return None
    if baseline == 0:
        deviation = float("inf") if current != 0 else 0.0
    else:
        deviation = (current - baseline) / abs(baseline)
    breached = abs(deviation) > tolerance
    return {
        "pipeline": pipeline,
        "metric": metric_name,
        "baseline": baseline,
        "current": current,
        "deviation": round(deviation, 6),
        "breached": breached,
    }


def list_baselines() -> Dict[str, Dict]:
    """Return a shallow copy of the full registry."""
    return {p: dict(metrics) for p, metrics in _BASELINES.items()}


def clear_baselines() -> None:
    """Wipe the in-memory registry (useful in tests)."""
    global _BASELINES
    _BASELINES = {}
