"""Metric aggregation: roll up multiple pipeline metrics into group-level summaries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from pipewatch.metrics import PipelineMetric


@dataclass
class AggregationResult:
    group: str
    pipelines: List[str]
    count: int
    ok: int
    warning: int
    critical: int
    avg_value: Optional[float]
    max_value: Optional[float]
    min_value: Optional[float]


def as_dict(result: AggregationResult) -> dict:
    return {
        "group": result.group,
        "pipelines": result.pipelines,
        "count": result.count,
        "ok": result.ok,
        "warning": result.warning,
        "critical": result.critical,
        "avg_value": result.avg_value,
        "max_value": result.max_value,
        "min_value": result.min_value,
    }


def aggregate_metrics(group: str, metrics: List[PipelineMetric]) -> AggregationResult:
    """Summarise a list of metrics into a single AggregationResult."""
    if not group or not group.strip():
        raise ValueError("group name must not be blank")

    ok = sum(1 for m in metrics if m.status == "ok")
    warning = sum(1 for m in metrics if m.status == "warning")
    critical = sum(1 for m in metrics if m.status == "critical")

    values = [m.value for m in metrics if m.value is not None]
    avg_value = sum(values) / len(values) if values else None
    max_value = max(values) if values else None
    min_value = min(values) if values else None

    return AggregationResult(
        group=group.strip(),
        pipelines=[m.pipeline for m in metrics],
        count=len(metrics),
        ok=ok,
        warning=warning,
        critical=critical,
        avg_value=avg_value,
        max_value=max_value,
        min_value=min_value,
    )


def aggregate_by_tag(tag: str, metrics: List[PipelineMetric]) -> AggregationResult:
    """Filter metrics whose tags include *tag* and aggregate them."""
    if not tag or not tag.strip():
        raise ValueError("tag must not be blank")
    tagged = [m for m in metrics if tag in (m.tags or [])]
    return aggregate_metrics(tag.strip(), tagged)


def aggregate_bulk(groups: Dict[str, List[PipelineMetric]]) -> List[AggregationResult]:
    """Aggregate multiple named groups at once."""
    return [aggregate_metrics(name, mlist) for name, mlist in groups.items()]
