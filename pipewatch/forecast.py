"""forecast.py — simple linear-trend forecasting for pipeline metrics."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from pipewatch.history import load_snapshots


@dataclass
class ForecastResult:
    pipeline: str
    metric_name: str
    horizon: int          # steps ahead
    predicted_value: float
    slope: float
    intercept: float
    confidence: str       # 'low' | 'medium' | 'high'
    data_points: int


def as_dict(result: ForecastResult) -> dict:
    return {
        "pipeline": result.pipeline,
        "metric_name": result.metric_name,
        "horizon": result.horizon,
        "predicted_value": round(result.predicted_value, 4),
        "slope": round(result.slope, 6),
        "intercept": round(result.intercept, 4),
        "confidence": result.confidence,
        "data_points": result.data_points,
    }


def _linear_fit(values: List[float]):
    """Return (slope, intercept) via least-squares."""
    n = len(values)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(values) / n
    denom = sum((x - mean_x) ** 2 for x in xs)
    if denom == 0:
        return 0.0, mean_y
    slope = sum((xs[i] - mean_x) * (values[i] - mean_y) for i in range(n)) / denom
    intercept = mean_y - slope * mean_x
    return slope, intercept


def _confidence(n: int) -> str:
    if n >= 20:
        return "high"
    if n >= 8:
        return "medium"
    return "low"


def forecast_pipeline(
    pipeline: str,
    metric_name: str,
    horizon: int = 1,
    history_dir: Optional[str] = None,
) -> Optional[ForecastResult]:
    """Forecast *horizon* steps ahead for a single pipeline metric."""
    snapshots = load_snapshots(history_dir=history_dir)
    values: List[float] = []
    for snap in snapshots:
        for entry in snap.get("metrics", []):
            if entry.get("pipeline") == pipeline and entry.get("name") == metric_name:
                try:
                    values.append(float(entry["value"]))
                except (KeyError, TypeError, ValueError):
                    pass
    if len(values) < 3:
        return None
    slope, intercept = _linear_fit(values)
    predicted = intercept + slope * (len(values) - 1 + horizon)
    return ForecastResult(
        pipeline=pipeline,
        metric_name=metric_name,
        horizon=horizon,
        predicted_value=predicted,
        slope=slope,
        intercept=intercept,
        confidence=_confidence(len(values)),
        data_points=len(values),
    )


def forecast_bulk(
    pipelines: List[str],
    metric_name: str,
    horizon: int = 1,
    history_dir: Optional[str] = None,
) -> List[ForecastResult]:
    """Run forecast for every pipeline in *pipelines*."""
    results = []
    for p in pipelines:
        r = forecast_pipeline(p, metric_name, horizon=horizon, history_dir=history_dir)
        if r is not None:
            results.append(r)
    return results
