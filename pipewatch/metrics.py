"""Metrics collection and evaluation for ETL pipeline health checks."""

import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PipelineMetric:
    """Represents a single captured metric from a pipeline run."""

    name: str
    value: float
    timestamp: float = field(default_factory=time.time)
    tags: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "value": self.value,
            "timestamp": self.timestamp,
            "tags": self.tags,
        }


def collect_metric(name: str, value: float, tags: Optional[dict] = None) -> PipelineMetric:
    """Create and return a PipelineMetric instance."""
    return PipelineMetric(name=name, value=value, tags=tags or {})


def evaluate_thresholds(metric: PipelineMetric, thresholds: dict) -> list[str]:
    """
    Compare a metric's value against configured thresholds.

    Args:
        metric: The PipelineMetric to evaluate.
        thresholds: Dict with optional keys 'warning' and 'critical'.

    Returns:
        A list of alert level strings that were breached, e.g. ['warning', 'critical'].
    """
    breaches = []
    warning = thresholds.get("warning")
    critical = thresholds.get("critical")

    if critical is not None and metric.value >= critical:
        breaches.append("critical")
    elif warning is not None and metric.value >= warning:
        breaches.append("warning")

    return breaches


def summarize_metrics(metrics: list[PipelineMetric]) -> dict:
    """Return basic summary statistics for a list of metrics."""
    if not metrics:
        return {}

    values = [m.value for m in metrics]
    return {
        "count": len(values),
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
        "latest": metrics[-1].value,
    }
