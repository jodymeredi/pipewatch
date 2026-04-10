"""Command-line interface for pipewatch.

Provides the main entry point and CLI commands for running pipeline
health checks, viewing reports, and managing alert configuration.
"""

import sys
import json
import argparse
import logging
from pathlib import Path

from pipewatch.config import load_config, validate_config
from pipewatch.metrics import collect_metric, evaluate_thresholds, summarize_metrics
from pipewatch.alerts import dispatch_alerts
from pipewatch.reporter import render_report

logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for the pipewatch CLI."""
    parser = argparse.ArgumentParser(
        prog="pipewatch",
        description="Lightweight CLI monitor for ETL pipeline health.",
    )
    parser.add_argument(
        "--config", "-c",
        metavar="PATH",
        default=None,
        help="Path to a pipewatch.yaml config file (default: auto-discover).",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format for the report (default: text).",
    )
    parser.add_argument(
        "--no-alerts",
        action="store_true",
        default=False,
        help="Suppress alert dispatching even when thresholds are breached.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=False,
        help="Enable verbose/debug logging.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    return parser


def configure_logging(verbose: bool) -> None:
    """Set up root logger based on verbosity flag."""
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        format="%(levelname)s %(name)s: %(message)s",
        level=level,
        stream=sys.stderr,
    )


def run(args: list[str] | None = None) -> int:
    """Main execution flow for the pipewatch CLI.

    Args:
        args: Argument list to parse (defaults to sys.argv[1:] when None).

    Returns:
        Exit code: 0 for success, 1 for breached thresholds, 2 for errors.
    """
    parser = build_parser()
    parsed = parser.parse_args(args)

    configure_logging(parsed.verbose)

    # Load and validate configuration
    try:
        config = load_config(parsed.config)
        validate_config(config)
    except (FileNotFoundError, ValueError) as exc:
        print(f"pipewatch: configuration error — {exc}", file=sys.stderr)
        return 2

    pipelines = config.get("pipelines", [])
    if not pipelines:
        print("pipewatch: no pipelines defined in configuration.", file=sys.stderr)
        return 2

    # Collect metrics for every configured pipeline
    metrics = []
    for pipeline_cfg in pipelines:
        try:
            metric = collect_metric(pipeline_cfg)
            metrics.append(metric)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to collect metric for %s: %s",
                           pipeline_cfg.get("name", "<unknown>"), exc)

    if not metrics:
        print("pipewatch: no metrics could be collected.", file=sys.stderr)
        return 2

    # Evaluate thresholds and optionally dispatch alerts
    breaches = evaluate_thresholds(metrics, config.get("thresholds", {}))

    if breaches and not parsed.no_alerts:
        dispatch_alerts(breaches, config.get("alerts", {}))

    # Render and print the report
    report = render_report(
        metrics=metrics,
        summary=summarize_metrics(metrics),
        output_format=parsed.output_format,
        config=config,
    )
    print(report)

    # Non-zero exit when any threshold was breached so CI pipelines can react
    return 1 if breaches else 0


def main() -> None:
    """Entry point registered in pyproject.toml / setup.cfg."""
    sys.exit(run())


if __name__ == "__main__":
    main()
