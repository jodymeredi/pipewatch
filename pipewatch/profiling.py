"""Pipeline execution profiling: track and analyze runtime durations."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_registry: Dict[str, List[float]] = {}
_max_samples: int = 100


def _now() -> float:
    return time.time()


@dataclass
class ProfileResult:
    pipeline: str
    count: int
    avg_duration: Optional[float]
    min_duration: Optional[float]
    max_duration: Optional[float]
    p95_duration: Optional[float]


def as_dict(result: ProfileResult) -> dict:
    return {
        "pipeline": result.pipeline,
        "count": result.count,
        "avg_duration": result.avg_duration,
        "min_duration": result.min_duration,
        "max_duration": result.max_duration,
        "p95_duration": result.p95_duration,
    }


def record_duration(pipeline: str, duration: float) -> None:
    """Record a single execution duration for a pipeline."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if duration < 0:
        raise ValueError("duration must be non-negative")
    samples = _registry.setdefault(pipeline, [])
    samples.append(duration)
    if len(samples) > _max_samples:
        _registry[pipeline] = samples[-_max_samples:]


def get_profile(pipeline: str) -> Optional[ProfileResult]:
    """Return profiling statistics for a pipeline, or None if no data."""
    pipeline = pipeline.strip()
    samples = _registry.get(pipeline)
    if not samples:
        return None
    sorted_samples = sorted(samples)
    count = len(sorted_samples)
    avg = sum(sorted_samples) / count
    p95_idx = max(0, int(count * 0.95) - 1)
    return ProfileResult(
        pipeline=pipeline,
        count=count,
        avg_duration=round(avg, 4),
        min_duration=sorted_samples[0],
        max_duration=sorted_samples[-1],
        p95_duration=sorted_samples[p95_idx],
    )


def clear_profile(pipeline: str) -> bool:
    """Remove profiling data for a pipeline. Returns True if data existed."""
    pipeline = pipeline.strip()
    if pipeline in _registry:
        del _registry[pipeline]
        return True
    return False


def list_profiles() -> List[str]:
    """Return list of pipeline names that have profiling data."""
    return list(_registry.keys())


def profile_all() -> List[ProfileResult]:
    """Return ProfileResult for every tracked pipeline."""
    return [r for p in list(_registry.keys()) if (r := get_profile(p)) is not None]
