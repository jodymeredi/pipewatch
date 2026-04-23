"""pipewatch.capping — per-pipeline metric value capping (floor/ceiling).

Allows operators to define hard lower and upper bounds on metric values
before they are evaluated against thresholds.  Values outside the cap
are clamped rather than rejected, preserving the pipeline run while
preventing runaway values from flooding alerts.
"""

from __future__ import annotations

from typing import Dict, List, Optional

_registry: Dict[str, Dict] = {}


def set_cap(
    pipeline: str,
    *,
    floor: Optional[float] = None,
    ceiling: Optional[float] = None,
) -> Dict:
    """Register or overwrite a cap rule for *pipeline*.

    At least one of *floor* or *ceiling* must be provided.
    If both are given, *floor* must be strictly less than *ceiling*.
    """
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if floor is None and ceiling is None:
        raise ValueError("at least one of floor or ceiling must be specified")
    if floor is not None and ceiling is not None and floor >= ceiling:
        raise ValueError("floor must be strictly less than ceiling")

    rule = {"pipeline": pipeline, "floor": floor, "ceiling": ceiling}
    _registry[pipeline] = rule
    return dict(rule)


def get_cap(pipeline: str) -> Optional[Dict]:
    """Return the cap rule for *pipeline*, or *None* if not set."""
    rule = _registry.get(pipeline.strip())
    return dict(rule) if rule else None


def remove_cap(pipeline: str) -> bool:
    """Remove the cap rule for *pipeline*.  Returns *True* if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_caps() -> List[Dict]:
    """Return a copy of all registered cap rules."""
    return [dict(r) for r in _registry.values()]


def apply_cap(pipeline: str, value: float) -> float:
    """Clamp *value* according to the cap rule registered for *pipeline*.

    If no rule exists the value is returned unchanged.
    """
    rule = _registry.get(pipeline.strip())
    if rule is None:
        return value
    if rule["floor"] is not None:
        value = max(value, rule["floor"])
    if rule["ceiling"] is not None:
        value = min(value, rule["ceiling"])
    return value
