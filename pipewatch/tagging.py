"""Tag-based filtering and grouping for pipeline metrics."""

from __future__ import annotations

from typing import Dict, List, Optional

# registry: tag_name -> set of pipeline names
_tag_index: Dict[str, set] = {}
# registry: pipeline_name -> set of tags
_pipeline_tags: Dict[str, set] = {}


def tag_pipeline(pipeline: str, tags: List[str]) -> Dict[str, List[str]]:
    """Associate *tags* with *pipeline*. Existing tags are preserved."""
    if not pipeline or not pipeline.strip():
        raise ValueError("pipeline name must be a non-empty string")
    if not tags:
        raise ValueError("tags list must not be empty")
    cleaned = [t.strip() for t in tags]
    if any(not t for t in cleaned):
        raise ValueError("tag entries must be non-empty strings")

    _pipeline_tags.setdefault(pipeline, set()).update(cleaned)
    for tag in cleaned:
        _tag_index.setdefault(tag, set()).add(pipeline)

    return {"pipeline": pipeline, "tags": sorted(_pipeline_tags[pipeline])}


def untag_pipeline(pipeline: str, tags: List[str]) -> bool:
    """Remove *tags* from *pipeline*. Returns True if any tag was removed."""
    if pipeline not in _pipeline_tags:
        return False
    before = len(_pipeline_tags[pipeline])
    for tag in tags:
        _pipeline_tags[pipeline].discard(tag)
        if tag in _tag_index:
            _tag_index[tag].discard(pipeline)
    return len(_pipeline_tags[pipeline]) < before


def get_tags(pipeline: str) -> List[str]:
    """Return sorted list of tags for *pipeline*."""
    return sorted(_pipeline_tags.get(pipeline, set()))


def pipelines_for_tag(tag: str) -> List[str]:
    """Return sorted list of pipelines that carry *tag*."""
    return sorted(_tag_index.get(tag, set()))


def filter_metrics_by_tag(metrics: list, tag: str) -> list:
    """Return only those metrics whose pipeline name carries *tag*."""
    tagged = _tag_index.get(tag, set())
    return [m for m in metrics if m.pipeline in tagged]


def list_tags() -> Dict[str, List[str]]:
    """Return a snapshot of all tags and their associated pipelines."""
    return {tag: sorted(pipelines) for tag, pipelines in _tag_index.items() if pipelines}


def clear_registry() -> None:  # test helper
    _tag_index.clear()
    _pipeline_tags.clear()
