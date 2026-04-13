"""Pipeline metric correlation — detect co-moving pipelines across snapshots."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from pipewatch.trend import _extract_series

_registry: Dict[str, List[str]] = {}  # pipeline -> correlated pipelines


@dataclass
class CorrelationResult:
    pipeline_a: str
    pipeline_b: str
    coefficient: float  # -1.0 to 1.0
    sample_size: int
    strong: bool = False


def as_dict(result: CorrelationResult) -> dict:
    return {
        "pipeline_a": result.pipeline_a,
        "pipeline_b": result.pipeline_b,
        "coefficient": round(result.coefficient, 4),
        "sample_size": result.sample_size,
        "strong": result.strong,
    }


def _pearson(xs: List[float], ys: List[float]) -> Optional[float]:
    """Compute Pearson r for two equal-length lists. Returns None if undefined."""
    n = len(xs)
    if n < 2:
        return None
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    num = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    den_x = sum((x - mean_x) ** 2 for x in xs) ** 0.5
    den_y = sum((y - mean_y) ** 2 for y in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return None
    return num / (den_x * den_y)


def correlate_pipelines(
    snapshots: List[dict],
    pipeline_a: str,
    pipeline_b: str,
    strong_threshold: float = 0.75,
) -> Optional[CorrelationResult]:
    """Compute correlation between two pipelines' metric values over shared snapshots."""
    series_a = _extract_series(snapshots, pipeline_a)
    series_b = _extract_series(snapshots, pipeline_b)
    min_len = min(len(series_a), len(series_b))
    if min_len < 2:
        return None
    xs = series_a[:min_len]
    ys = series_b[:min_len]
    coeff = _pearson(xs, ys)
    if coeff is None:
        return None
    return CorrelationResult(
        pipeline_a=pipeline_a,
        pipeline_b=pipeline_b,
        coefficient=coeff,
        sample_size=min_len,
        strong=abs(coeff) >= strong_threshold,
    )


def find_correlated_pairs(
    snapshots: List[dict],
    pipelines: List[str],
    strong_threshold: float = 0.75,
) -> List[CorrelationResult]:
    """Return all strongly correlated pipeline pairs from a list of candidates."""
    results: List[CorrelationResult] = []
    for i, a in enumerate(pipelines):
        for b in pipelines[i + 1 :]:
            r = correlate_pipelines(snapshots, a, b, strong_threshold)
            if r is not None:
                results.append(r)
    results.sort(key=lambda r: abs(r.coefficient), reverse=True)
    return results
