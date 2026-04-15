"""pipewatch.sampling — Control which pipelines are sampled and at what rate."""

from __future__ import annotations

import random
from typing import Dict, List, Optional

from pipewatch.metrics import PipelineMetric

_registry: Dict[str, Dict] = {}
_DEFAULT_RATE: float = 1.0  # 100 % — always sample


def set_sample_rate(pipeline: str, rate: float) -> Dict:
    """Register a sampling rate (0.0–1.0) for *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if not (0.0 < rate <= 1.0):
        raise ValueError("rate must be in the range (0.0, 1.0]")
    _registry[pipeline] = {"pipeline": pipeline, "rate": rate}
    return dict(_registry[pipeline])


def get_sample_rate(pipeline: str) -> float:
    """Return the configured sampling rate for *pipeline* (default 1.0)."""
    entry = _registry.get(pipeline.strip())
    return entry["rate"] if entry else _DEFAULT_RATE


def remove_sample_rate(pipeline: str) -> bool:
    """Remove the sampling rule for *pipeline*. Returns True if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_sample_rates() -> List[Dict]:
    """Return a copy of all registered sampling rules."""
    return [dict(v) for v in _registry.values()]


def should_sample(pipeline: str) -> bool:
    """Return True if this pipeline should be sampled on this call."""
    rate = get_sample_rate(pipeline)
    return random.random() < rate


def filter_sampled_metrics(
    metrics: List[PipelineMetric],
    seed: Optional[int] = None,
) -> List[PipelineMetric]:
    """Return only the metrics whose pipeline passes the sampling check.

    *seed* is accepted for deterministic testing.
    """
    if seed is not None:
        random.seed(seed)
    return [m for m in metrics if should_sample(m.pipeline)]
