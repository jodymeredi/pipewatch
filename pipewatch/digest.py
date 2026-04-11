"""digest.py – Periodic summary digest for pipeline health reports.

Builds a digest (daily/hourly) from recorded snapshots and dispatches
it through the registered alert handlers.
"""

from __future__ import annotations

import datetime
from typing import Any

from pipewatch.history import load_snapshots
from pipewatch.alerts import dispatch_alerts
from pipewatch.metrics import PipelineMetric, evaluate_thresholds


def _window_start(period: str) -> datetime.datetime:
    """Return the UTC start of the current digest window."""
    now = datetime.datetime.utcnow()
    if period == "hourly":
        return now.replace(minute=0, second=0, microsecond=0)
    # default: daily
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def collect_window_metrics(
    history_dir: str,
    pipeline: str,
    period: str = "daily",
) -> list[dict[str, Any]]:
    """Return snapshot entries for *pipeline* within the current window."""
    cutoff = _window_start(period)
    entries = []
    for snap in load_snapshots(history_dir, pipeline):
        recorded_at_raw = snap.get("recorded_at", "")
        try:
            ts = datetime.datetime.fromisoformat(recorded_at_raw.replace("Z", "+00:00"))
            ts_naive = ts.replace(tzinfo=None)
        except (ValueError, AttributeError):
            continue
        if ts_naive >= cutoff:
            entries.append(snap)
    return entries


def build_digest(
    history_dir: str,
    pipelines: list[str],
    thresholds: dict[str, Any],
    period: str = "daily",
) -> dict[str, Any]:
    """Aggregate window metrics and evaluate thresholds for each pipeline."""
    summary: dict[str, Any] = {
        "period": period,
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "pipelines": {},
    }
    for pipeline in pipelines:
        entries = collect_window_metrics(history_dir, pipeline, period)
        if not entries:
            summary["pipelines"][pipeline] = {"samples": 0, "alerts": []}
            continue

        metrics: list[PipelineMetric] = []
        for e in entries:
            try:
                m = PipelineMetric(
                    pipeline=e["pipeline"],
                    metric=e["metric"],
                    value=float(e["value"]),
                    tags=e.get("tags", {}),
                )
                metrics.append(m)
            except (KeyError, TypeError, ValueError):
                continue

        breaches = evaluate_thresholds(metrics, thresholds)
        summary["pipelines"][pipeline] = {
            "samples": len(metrics),
            "alerts": [str(b) for b in breaches],
        }
    return summary


def dispatch_digest(
    digest: dict[str, Any],
    config: dict[str, Any],
) -> None:
    """Send the digest through registered alert handlers."""
    all_alerts: list[str] = []
    for pipeline, info in digest.get("pipelines", {}).items():
        for alert in info.get("alerts", []):
            all_alerts.append(f"[{pipeline}] {alert}")
    if all_alerts:
        dispatch_alerts(all_alerts, config)
