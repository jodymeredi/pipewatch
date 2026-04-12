"""Pipeline label management — attach freeform key/value labels to pipelines.

Labels differ from tags in that they carry a value (e.g. owner=alice,
env=production) rather than being plain membership tokens.
"""
from __future__ import annotations

from typing import Dict, List, Optional

# Registry: pipeline -> {key: value}
_registry: Dict[str, Dict[str, str]] = {}


def set_label(pipeline: str, key: str, value: str) -> Dict[str, str]:
    """Set or overwrite a single label on *pipeline*.

    Returns the full label map for the pipeline after the update.
    """
    if not pipeline or not pipeline.strip():
        raise ValueError("pipeline name must not be blank")
    if not key or not key.strip():
        raise ValueError("label key must not be blank")
    _registry.setdefault(pipeline, {})[key] = value
    return dict(_registry[pipeline])


def remove_label(pipeline: str, key: str) -> bool:
    """Remove *key* from *pipeline*'s labels.

    Returns True if the label existed and was removed, False otherwise.
    """
    labels = _registry.get(pipeline, {})
    if key in labels:
        del labels[key]
        if not labels:
            del _registry[pipeline]
        return True
    return False


def get_labels(pipeline: str) -> Dict[str, str]:
    """Return a copy of all labels for *pipeline* (empty dict if none)."""
    return dict(_registry.get(pipeline, {}))


def get_label(pipeline: str, key: str) -> Optional[str]:
    """Return the value of *key* for *pipeline*, or None if absent."""
    return _registry.get(pipeline, {}).get(key)


def pipelines_with_label(key: str, value: Optional[str] = None) -> List[str]:
    """Return pipelines that have *key* set (optionally matching *value*)."""
    result = []
    for pipeline, labels in _registry.items():
        if key in labels:
            if value is None or labels[key] == value:
                result.append(pipeline)
    return sorted(result)


def list_labels() -> Dict[str, Dict[str, str]]:
    """Return a copy of the entire label registry."""
    return {p: dict(lbs) for p, lbs in _registry.items()}


def clear_labels(pipeline: str) -> int:
    """Remove all labels from *pipeline*. Returns number of labels removed."""
    labels = _registry.pop(pipeline, {})
    return len(labels)
