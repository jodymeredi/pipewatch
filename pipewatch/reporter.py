"""reporter.py — Formats and outputs pipeline health summaries to stdout or file."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import IO, List, Literal, Optional

from pipewatch.metrics import PipelineMetric, summarize_metrics

OutputFormat = Literal["text", "json"]


def _utcnow() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


def format_text(metrics: List[PipelineMetric], summary: dict) -> str:
    """Return a human-readable report string."""
    lines: List[str] = [
        f"PipeWatch Report  [{_utcnow()}]",
        "-" * 44,
    ]
    for m in metrics:
        status_icon = {"ok": "✓", "warning": "!", "critical": "✗"}.get(m.status, "?")
        tag_str = ""
        if m.tags:
            tag_str = "  tags=" + ",".join(f"{k}:{v}" for k, v in m.tags.items())
        lines.append(
            f"  [{status_icon}] {m.pipeline:<24} {m.metric_name:<16} "
            f"{m.value:>10.4f}{tag_str}"
        )
    lines.append("-" * 44)
    lines.append(
        f"  Total: {summary['total']}  "
        f"OK: {summary['ok']}  "
        f"Warning: {summary['warning']}  "
        f"Critical: {summary['critical']}"
    )
    return "\n".join(lines)


def format_json(metrics: List[PipelineMetric], summary: dict) -> str:
    """Return a JSON-serialisable report string."""
    payload = {
        "generated_at": _utcnow(),
        "summary": summary,
        "metrics": [
            {
                "pipeline": m.pipeline,
                "metric_name": m.metric_name,
                "value": m.value,
                "status": m.status,
                "timestamp": m.timestamp,
                "tags": m.tags or {},
            }
            for m in metrics
        ],
    }
    return json.dumps(payload, indent=2)


def render_report(
    metrics: List[PipelineMetric],
    fmt: OutputFormat = "text",
    output: Optional[IO[str]] = None,
) -> str:
    """Render a health report and write it to *output* (default: stdout).

    Returns the rendered string so callers can capture it if needed.
    """
    if output is None:
        output = sys.stdout

    summary = summarize_metrics(metrics)

    if fmt == "json":
        rendered = format_json(metrics, summary)
    else:
        rendered = format_text(metrics, summary)

    print(rendered, file=output)
    return rendered
