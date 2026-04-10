"""Alert dispatch logic for pipewatch pipeline health monitoring."""

import logging
from typing import Callable, Optional

from pipewatch.metrics import PipelineMetric, evaluate_thresholds

logger = logging.getLogger(__name__)

# Registry of named alert handlers: name -> callable(metric, level)
_HANDLERS: dict[str, Callable] = {}


def register_handler(name: str, handler: Callable) -> None:
    """Register a named alert handler function."""
    _HANDLERS[name] = handler


def get_handler(name: str) -> Optional[Callable]:
    """Retrieve a registered handler by name, or None."""
    return _HANDLERS.get(name)


def log_alert(metric: PipelineMetric, level: str) -> None:
    """Built-in handler that logs alerts to the standard logger."""
    log_fn = logger.critical if level == "critical" else logger.warning
    log_fn(
        "[pipewatch] %s alert — metric '%s' value=%.4f tags=%s",
        level.upper(),
        metric.name,
        metric.value,
        metric.tags,
    )


# Register the default log handler automatically
register_handler("log", log_alert)


def dispatch_alerts(
    metric: PipelineMetric,
    thresholds: dict,
    handler_names: Optional[list[str]] = None,
) -> list[str]:
    """
    Evaluate thresholds for a metric and dispatch to registered handlers.

    Args:
        metric: The PipelineMetric to check.
        thresholds: Dict with optional 'warning' / 'critical' keys.
        handler_names: List of handler names to invoke. Defaults to ['log'].

    Returns:
        List of breached alert levels.
    """
    if handler_names is None:
        handler_names = ["log"]

    breaches = evaluate_thresholds(metric, thresholds)

    for level in breaches:
        for name in handler_names:
            handler = get_handler(name)
            if handler is None:
                logger.warning("[pipewatch] No handler registered for '%s'", name)
                continue
            try:
                handler(metric, level)
            except Exception as exc:  # pylint: disable=broad-except
                logger.error(
                    "[pipewatch] Handler '%s' raised an exception: %s", name, exc
                )

    return breaches
