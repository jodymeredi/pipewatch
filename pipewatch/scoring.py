"""Pipeline health scoring — compute a numeric health score for each pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import PipelineMetric

# Weight per alert level (higher = worse)
_LEVEL_WEIGHTS: Dict[str, float] = {
    "ok": 0.0,
    "warning": 0.4,
    "critical": 1.0,
}

_REGISTRY: Dict[str, dict] = {}


@dataclass
class ScoreResult:
    pipeline: str
    score: float          # 0.0 (healthy) – 100.0 (worst)
    level: str
    contributors: List[str] = field(default_factory=list)


def as_dict(result: ScoreResult) -> dict:
    return {
        "pipeline": result.pipeline,
        "score": result.score,
        "level": result.level,
        "contributors": result.contributors,
    }


def set_weight(level: str, weight: float) -> dict:
    """Override the default weight for a given alert level."""
    level = level.strip().lower()
    if level not in _LEVEL_WEIGHTS:
        raise ValueError(f"Unknown level: {level!r}")
    if not (0.0 <= weight <= 1.0):
        raise ValueError("Weight must be between 0.0 and 1.0")
    _LEVEL_WEIGHTS[level] = weight
    return dict(_LEVEL_WEIGHTS)


def score_pipeline(pipeline: str, metrics: List[PipelineMetric]) -> ScoreResult:
    """Compute a health score in [0, 100] for *pipeline* from its metrics."""
    pipeline_metrics = [m for m in metrics if m.pipeline == pipeline]
    if not pipeline_metrics:
        return ScoreResult(pipeline=pipeline, score=0.0, level="ok", contributors=[])

    contributors: List[str] = []
    total_weight = 0.0
    for m in pipeline_metrics:
        lvl = (m.status or "ok").lower()
        w = _LEVEL_WEIGHTS.get(lvl, 0.0)
        if w > 0:
            contributors.append(f"{m.pipeline}:{m.name}={lvl}")
        total_weight += w

    raw = (total_weight / len(pipeline_metrics)) * 100.0
    score = min(round(raw, 2), 100.0)

    if score >= 60.0:
        level = "critical"
    elif score >= 20.0:
        level = "warning"
    else:
        level = "ok"

    return ScoreResult(pipeline=pipeline, score=score, level=level, contributors=contributors)


def score_all(metrics: List[PipelineMetric]) -> List[ScoreResult]:
    """Score every distinct pipeline present in *metrics*."""
    pipelines = list(dict.fromkeys(m.pipeline for m in metrics))
    return [score_pipeline(p, metrics) for p in pipelines]
