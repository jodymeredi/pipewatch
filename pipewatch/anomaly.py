"""Anomaly detection for pipeline metrics using z-score against historical snapshots."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import load_snapshots


@dataclass
class AnomalyResult:
    pipeline: str
    current_value: float
    mean: float
    stddev: float
    z_score: float
    is_anomaly: bool
    threshold: float
    tags: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "current_value": self.current_value,
            "mean": round(self.mean, 4),
            "stddev": round(self.stddev, 4),
            "z_score": round(self.z_score, 4),
            "is_anomaly": self.is_anomaly,
            "threshold": self.threshold,
            "tags": self.tags,
        }


def _compute_stats(values: List[float]):
    """Return (mean, stddev) for a list of floats."""
    n = len(values)
    if n == 0:
        return 0.0, 0.0
    mean = sum(values) / n
    variance = sum((v - mean) ** 2 for v in values) / n
    return mean, math.sqrt(variance)


def detect_anomaly(
    pipeline: str,
    current_value: float,
    history_dir: Optional[str] = None,
    z_threshold: float = 2.5,
    min_samples: int = 5,
    tags: Optional[dict] = None,
) -> Optional[AnomalyResult]:
    """Compare *current_value* against historical values for *pipeline*.

    Returns an :class:`AnomalyResult` when enough history is available,
    or ``None`` when there are fewer than *min_samples* data points.
    """
    snapshots = load_snapshots(history_dir=history_dir)
    historical: List[float] = []
    for snapshot in snapshots:
        for entry in snapshot.get("metrics", []):
            if entry.get("pipeline") == pipeline:
                try:
                    historical.append(float(entry["value"]))
                except (KeyError, TypeError, ValueError):
                    pass

    if len(historical) < min_samples:
        return None

    mean, stddev = _compute_stats(historical)
    if stddev == 0.0:
        z_score = 0.0
    else:
        z_score = abs(current_value - mean) / stddev

    return AnomalyResult(
        pipeline=pipeline,
        current_value=current_value,
        mean=mean,
        stddev=stddev,
        z_score=z_score,
        is_anomaly=z_score >= z_threshold,
        threshold=z_threshold,
        tags=tags or {},
    )


def detect_anomalies_bulk(
    metrics: list,
    history_dir: Optional[str] = None,
    z_threshold: float = 2.5,
    min_samples: int = 5,
) -> List[AnomalyResult]:
    """Run anomaly detection for a list of metric dicts."""
    results = []
    for m in metrics:
        result = detect_anomaly(
            pipeline=m["pipeline"],
            current_value=float(m["value"]),
            history_dir=history_dir,
            z_threshold=z_threshold,
            min_samples=min_samples,
            tags=m.get("tags", {}),
        )
        if result is not None:
            results.append(result)
    return results
