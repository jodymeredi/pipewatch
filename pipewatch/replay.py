"""Replay historical snapshots through alert evaluation for back-testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pipewatch.history import load_snapshots
from pipewatch.metrics import PipelineMetric, evaluate_thresholds
from pipewatch.alerts import dispatch_alerts


@dataclass
class ReplayResult:
    pipeline: str
    snapshot_time: str
    status: str
    breaches: list[dict[str, Any]] = field(default_factory=list)
    alerts_dispatched: int = 0


def as_dict(result: ReplayResult) -> dict[str, Any]:
    return {
        "pipeline": result.pipeline,
        "snapshot_time": result.snapshot_time,
        "status": result.status,
        "breaches": result.breaches,
        "alerts_dispatched": result.alerts_dispatched,
    }


def replay_snapshots(
    history_dir: str,
    pipeline: str | None = None,
    dry_run: bool = True,
    config: dict[str, Any] | None = None,
) -> list[ReplayResult]:
    """Load historical snapshots and replay alert evaluation against them.

    Args:
        history_dir: Directory containing snapshot files.
        pipeline: If given, only replay entries for this pipeline.
        dry_run: When True, evaluate but do not actually dispatch alerts.
        config: Optional threshold config forwarded to evaluate_thresholds.

    Returns:
        List of ReplayResult, one per snapshot entry processed.
    """
    snapshots = load_snapshots(history_dir)
    results: list[ReplayResult] = []
    cfg = config or {}

    for entry in snapshots:
        recorded_at = entry.get("recorded_at", "unknown")
        metrics_raw = entry.get("metrics", [])

        for m in metrics_raw:
            name = m.get("pipeline", "")
            if pipeline and name != pipeline:
                continue

            metric = PipelineMetric(
                pipeline=name,
                value=m.get("value", 0.0),
                unit=m.get("unit", ""),
                tags=m.get("tags", {}),
            )
            breaches = evaluate_thresholds(metric, cfg)
            dispatched = 0
            if breaches and not dry_run:
                dispatch_alerts(breaches)
                dispatched = len(breaches)

            status = "ok" if not breaches else breaches[0].get("level", "warning")
            results.append(
                ReplayResult(
                    pipeline=name,
                    snapshot_time=recorded_at,
                    status=status,
                    breaches=breaches,
                    alerts_dispatched=dispatched,
                )
            )

    return results


def summarize_replay(results: list[ReplayResult]) -> dict[str, Any]:
    """Return aggregate counts across all replay results."""
    total = len(results)
    ok = sum(1 for r in results if r.status == "ok")
    breaching = total - ok
    return {"total": total, "ok": ok, "breaching": breaching}


def filter_results_by_status(
    results: list[ReplayResult], status: str
) -> list[ReplayResult]:
    """Return only the replay results that match the given status.

    Args:
        results: Full list of ReplayResult objects from a replay run.
        status: Status string to filter by, e.g. ``"ok"``, ``"warning"``,
            or ``"critical"``.

    Returns:
        A new list containing only results whose status equals *status*.
    """
    return [r for r in results if r.status == status]
