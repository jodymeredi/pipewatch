"""pipewatch.normalization – metric value normalization rules.

Allows defining per-pipeline normalization functions (min-max scaling,
z-score, clamp) so that metrics are comparable across pipelines with
different natural value ranges before threshold evaluation.
"""
from __future__ import annotations

import math
from typing import Dict, Optional, Tuple

# Registry: pipeline -> {method, params}
_registry: Dict[str, dict] = {}

_VALID_METHODS = {"minmax", "zscore", "clamp"}


def set_normalization(
    pipeline: str,
    method: str,
    *,
    min_val: float = 0.0,
    max_val: float = 1.0,
    mean: float = 0.0,
    std: float = 1.0,
    clamp_low: Optional[float] = None,
    clamp_high: Optional[float] = None,
) -> dict:
    """Register a normalization rule for *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    method = method.strip().lower()
    if method not in _VALID_METHODS:
        raise ValueError(f"method must be one of {sorted(_VALID_METHODS)}")
    if method == "minmax" and math.isclose(min_val, max_val):
        raise ValueError("min_val and max_val must differ for minmax normalization")
    if method == "zscore" and math.isclose(std, 0.0):
        raise ValueError("std must be non-zero for zscore normalization")
    rule = {"pipeline": pipeline, "method": method}
    if method == "minmax":
        rule["min_val"] = min_val
        rule["max_val"] = max_val
    elif method == "zscore":
        rule["mean"] = mean
        rule["std"] = std
    elif method == "clamp":
        rule["clamp_low"] = clamp_low
        rule["clamp_high"] = clamp_high
    _registry[pipeline] = rule
    return dict(rule)


def get_normalization(pipeline: str) -> Optional[dict]:
    """Return the normalization rule for *pipeline*, or None."""
    rule = _registry.get(pipeline.strip())
    return dict(rule) if rule else None


def remove_normalization(pipeline: str) -> bool:
    """Remove the rule for *pipeline*. Returns True if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_normalizations() -> list:
    """Return a copy of all registered normalization rules."""
    return [dict(r) for r in _registry.values()]


def normalize_value(pipeline: str, value: float) -> Tuple[float, bool]:
    """Apply the registered rule to *value*.

    Returns ``(normalized_value, was_applied)``.
    If no rule is registered, returns ``(value, False)``.
    """
    rule = _registry.get(pipeline.strip())
    if rule is None:
        return value, False
    method = rule["method"]
    if method == "minmax":
        lo, hi = rule["min_val"], rule["max_val"]
        result = (value - lo) / (hi - lo)
    elif method == "zscore":
        result = (value - rule["mean"]) / rule["std"]
    elif method == "clamp":
        result = value
        if rule.get("clamp_low") is not None:
            result = max(result, rule["clamp_low"])
        if rule.get("clamp_high") is not None:
            result = min(result, rule["clamp_high"])
    else:
        return value, False
    return result, True
