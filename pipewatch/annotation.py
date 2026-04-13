"""Pipeline annotation support — attach free-form notes to pipelines."""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

_registry: Dict[str, List[Dict[str, Any]]] = {}


def _now() -> float:
    return time.time()


def add_annotation(
    pipeline: str,
    note: str,
    author: str = "system",
    tags: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Attach a timestamped note to *pipeline*."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if not note.strip():
        raise ValueError("annotation note must not be blank")

    entry: Dict[str, Any] = {
        "pipeline": pipeline,
        "note": note.strip(),
        "author": author.strip() or "system",
        "tags": sorted(set(tags or [])),
        "created_at": _now(),
    }
    _registry.setdefault(pipeline, []).append(entry)
    return dict(entry)


def get_annotations(pipeline: str) -> List[Dict[str, Any]]:
    """Return all annotations for *pipeline* (oldest first)."""
    return [dict(e) for e in _registry.get(pipeline.strip(), [])]


def remove_annotations(pipeline: str) -> int:
    """Delete all annotations for *pipeline*. Returns count removed."""
    pipeline = pipeline.strip()
    removed = _registry.pop(pipeline, [])
    return len(removed)


def list_annotated_pipelines() -> List[str]:
    """Return sorted list of pipelines that have at least one annotation."""
    return sorted(k for k, v in _registry.items() if v)


def search_annotations(keyword: str) -> List[Dict[str, Any]]:
    """Return all annotations whose note contains *keyword* (case-insensitive)."""
    keyword = keyword.lower()
    results = []
    for entries in _registry.values():
        for entry in entries:
            if keyword in entry["note"].lower():
                results.append(dict(entry))
    return results


def clear_all() -> None:  # test helper
    _registry.clear()
