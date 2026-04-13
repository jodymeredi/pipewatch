"""Trend analysis for pipeline metrics over historical snapshots."""

from __future__ import annotations

from typing import List, Optional
from dataclasses import dataclass

from pipewatch.history import load_snapshots


@dataclass
class TrendResult:
    pipeline: str
    metric_name: str
    direction: str          # 'improving', 'degrading', 'stable', 'insufficient_data'
    first_value: Optional[float]
    last_value: Optional[float]
    sample_count: int
    delta: Optional[float]


def _extract_series(snapshots: list, pipeline: str, metric_name: str) -> List[float]:
    """Pull an ordered list of numeric values for a given pipeline/metric."""
    series: List[float] = []
    for snap in snapshots:
        for entry in snap.get("metrics", []):
            if (
                entry.get("pipeline") == pipeline
                and entry.get("name") == metric_name
                and entry.get("value") is not None
            ):
                try:
                    series.append(float(entry["value"]))
                except (TypeError, ValueError):
                    pass
    return series


def analyze_trend(
    pipeline: str,
    metric_name: str,
    history_dir: str,
    min_samples: int = 3,
    threshold_pct: float = 5.0,
) -> TrendResult:
    """Analyse trend direction for a single pipeline metric.

    Parameters
    ----------
    pipeline:      pipeline identifier string
    metric_name:   name of the metric to analyse
    history_dir:   directory passed to load_snapshots
    min_samples:   minimum data points required to determine direction
    threshold_pct: percentage change considered significant
    """
    snapshots = load_snapshots(history_dir)
    series = _extract_series(snapshots, pipeline, metric_name)

    if len(series) < min_samples:
        return TrendResult(
            pipeline=pipeline,
            metric_name=metric_name,
            direction="insufficient_data",
            first_value=series[0] if series else None,
            last_value=series[-1] if series else None,
            sample_count=len(series),
            delta=None,
        )

    first, last = series[0], series[-1]
    delta = last - first
    pct_change = (delta / first * 100) if first != 0 else 0.0

    if abs(pct_change) < threshold_pct:
        direction = "stable"
    elif pct_change > 0:
        direction = "degrading"
    else:
        direction = "improving"

    return TrendResult(
        pipeline=pipeline,
        metric_name=metric_name,
        direction=direction,
        first_value=first,
        last_value=last,
        sample_count=len(series),
        delta=round(delta, 6),
    )


def filter_trends(trends: List[TrendResult], direction: str) -> List[TrendResult]:
    """Return only the trends matching the given direction.

    Parameters
    ----------
    trends:    list of TrendResult objects to filter
    direction: one of 'improving', 'degrading', 'stable', 'insufficient_data'
    """
    return [t for t in trends if t.direction == direction]


def summarize_trends(trends: List[TrendResult]) -> dict:
    """Return a simple count summary of trend directions."""
    summary: dict = {"improving": 0, "degrading": 0, "stable": 0, "insufficient_data": 0}
    for t in trends:
        summary[t.direction] = summary.get(t.direction, 0) + 1
    return summary
