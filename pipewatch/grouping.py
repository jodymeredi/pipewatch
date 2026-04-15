"""Pipeline grouping — organise pipelines into named groups for bulk operations."""

from __future__ import annotations

from typing import Dict, List, Optional

from pipewatch.metrics import PipelineMetric

# { group_name: [pipeline_name, ...] }
_registry: Dict[str, List[str]] = {}


def create_group(group: str, pipelines: List[str]) -> Dict:
    """Create or replace a named group of pipeline names."""
    group = group.strip()
    if not group:
        raise ValueError("group name must not be blank")
    if not pipelines:
        raise ValueError("pipelines list must not be empty")
    cleaned = [p.strip() for p in pipelines]
    if any(p == "" for p in cleaned):
        raise ValueError("pipeline entries must not be blank")
    _registry[group] = list(dict.fromkeys(cleaned))  # deduplicate, preserve order
    return {"group": group, "pipelines": _registry[group]}


def remove_group(group: str) -> bool:
    """Remove a group by name.  Returns True if it existed."""
    return _registry.pop(group, None) is not None


def get_group(group: str) -> Optional[List[str]]:
    """Return a copy of the pipeline list for *group*, or None if absent."""
    entry = _registry.get(group)
    return list(entry) if entry is not None else None


def list_groups() -> Dict[str, List[str]]:
    """Return a shallow copy of the entire group registry."""
    return {g: list(ps) for g, ps in _registry.items()}


def add_pipeline_to_group(group: str, pipeline: str) -> Dict:
    """Append *pipeline* to an existing group (no-op if already present)."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if group not in _registry:
        raise KeyError(f"group '{group}' does not exist")
    if pipeline not in _registry[group]:
        _registry[group].append(pipeline)
    return {"group": group, "pipelines": list(_registry[group])}


def remove_pipeline_from_group(group: str, pipeline: str) -> bool:
    """Remove *pipeline* from *group*.  Returns True if it was present."""
    if group not in _registry:
        return False
    try:
        _registry[group].remove(pipeline)
        return True
    except ValueError:
        return False


def find_groups_for_pipeline(pipeline: str) -> List[str]:
    """Return the names of all groups that contain *pipeline*.

    Useful for auditing which groups a given pipeline belongs to, or for
    cleaning up references before renaming/deleting a pipeline.

    Args:
        pipeline: The exact pipeline name to search for.

    Returns:
        A sorted list of group names that include *pipeline*.
    """
    return sorted(group for group, members in _registry.items() if pipeline in members)


def filter_metrics_by_group(group: str, metrics: List[PipelineMetric]) -> List[PipelineMetric]:
    """Return only the metrics whose pipeline name belongs to *group*."""
    members = set(_registry.get(group, []))
    return [m for m in metrics if m.pipeline in members]
