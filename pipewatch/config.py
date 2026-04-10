"""Configuration loader for pipewatch.

Loads pipeline definitions and alert thresholds from a YAML config file.
"""

import os
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("pipewatch.yaml")

DEFAULT_CONFIG: dict[str, Any] = {
    "pipelines": [],
    "alert": {
        "max_failure_rate": 0.1,
        "max_latency_seconds": 300,
        "notify": "log",
    },
    "check_interval_seconds": 60,
}


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load configuration from a YAML file, falling back to defaults.

    Args:
        path: Path to the YAML config file. Defaults to ``pipewatch.yaml``
              in the current working directory or the ``PIPEWATCH_CONFIG``
              environment variable.

    Returns:
        Merged configuration dictionary.
    """
    config_path = Path(
        path
        or os.environ.get("PIPEWATCH_CONFIG", DEFAULT_CONFIG_PATH)
    )

    config = dict(DEFAULT_CONFIG)

    if config_path.exists():
        with config_path.open("r") as fh:
            user_config = yaml.safe_load(fh) or {}
        # Shallow-merge top-level keys; alert block merged separately
        config.update({k: v for k, v in user_config.items() if k != "alert"})
        if "alert" in user_config:
            config["alert"] = {**DEFAULT_CONFIG["alert"], **user_config["alert"]}
    else:
        if path is not None:
            raise FileNotFoundError(f"Config file not found: {config_path}")

    return config


def validate_config(config: dict[str, Any]) -> list[str]:
    """Return a list of validation error messages (empty means valid)."""
    errors: list[str] = []

    if not isinstance(config.get("pipelines"), list):
        errors.append("'pipelines' must be a list.")
    else:
        for i, pipeline in enumerate(config["pipelines"]):
            if "name" not in pipeline:
                errors.append(f"Pipeline at index {i} is missing 'name'.")
            if "source" not in pipeline:
                errors.append(f"Pipeline at index {i} is missing 'source'.")

    alert = config.get("alert", {})
    if not 0.0 <= float(alert.get("max_failure_rate", 0)) <= 1.0:
        errors.append("alert.max_failure_rate must be between 0.0 and 1.0.")
    if float(alert.get("max_latency_seconds", 1)) <= 0:
        errors.append("alert.max_latency_seconds must be positive.")

    return errors
