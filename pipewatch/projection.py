"""pipewatch.projection — project future metric values based on trend + forecast."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from pipewatch.forecast import forecast_pipeline, ForecastResult
from pipewatch.trend import analyze_trend, TrendResult


@dataclass
class ProjectionResult:
    pipeline: str
    current_value: Optional[float]
    projected_value: Optional[float]
    horizon_steps: int
    trend_direction: Optional[str]  # "up" | "down" | "stable" | None
    pct_change: Optional[float]
    confidence: Optional[float]
    status: str  # "ok" | "rising" | "falling" | "insufficient_data"
    notes: list[str] = field(default_factory=list)


def as_dict(r: ProjectionResult) -> dict:
    return {
        "pipeline": r.pipeline,
        "current_value": r.current_value,
        "projected_value": r.projected_value,
        "horizon_steps": r.horizon_steps,
        "trend_direction": r.trend_direction,
        "pct_change": r.pct_change,
        "confidence": r.confidence,
        "status": r.status,
        "notes": list(r.notes),
    }


def project_pipeline(
    pipeline: str,
    history_dir: str,
    horizon: int = 3,
    rising_threshold: float = 5.0,
    falling_threshold: float = -5.0,
) -> ProjectionResult:
    """Combine trend + forecast to produce a forward-looking projection."""
    forecast: Optional[ForecastResult] = forecast_pipeline(
        pipeline, history_dir, horizon=horizon
    )
    trend: Optional[TrendResult] = analyze_trend(pipeline, history_dir)

    if forecast is None or forecast.predicted_value is None:
        return ProjectionResult(
            pipeline=pipeline,
            current_value=None,
            projected_value=None,
            horizon_steps=horizon,
            trend_direction=None,
            pct_change=None,
            confidence=None,
            status="insufficient_data",
            notes=["Not enough history to project."],
        )

    current = forecast.last_value
    projected = forecast.predicted_value
    pct_change: Optional[float] = None
    if current is not None and current != 0:
        pct_change = round((projected - current) / abs(current) * 100, 2)

    trend_dir = trend.direction if trend else None

    if pct_change is None:
        status = "ok"
    elif pct_change >= rising_threshold:
        status = "rising"
    elif pct_change <= falling_threshold:
        status = "falling"
    else:
        status = "ok"

    notes: list[str] = []
    if trend_dir == "up" and status == "rising":
        notes.append("Trend confirms upward projection.")
    elif trend_dir == "down" and status == "falling":
        notes.append("Trend confirms downward projection.")

    return ProjectionResult(
        pipeline=pipeline,
        current_value=current,
        projected_value=round(projected, 4),
        horizon_steps=horizon,
        trend_direction=trend_dir,
        pct_change=pct_change,
        confidence=forecast.confidence,
        status=status,
        notes=notes,
    )


def project_bulk(
    pipelines: list[str],
    history_dir: str,
    horizon: int = 3,
) -> list[ProjectionResult]:
    """Run projections for multiple pipelines."""
    return [project_pipeline(p, history_dir, horizon=horizon) for p in pipelines]
