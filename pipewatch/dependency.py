"""Pipeline dependency tracking — define upstream/downstream relationships
and detect pipelines that should not run while a dependency is unhealthy."""

from __future__ import annotations

from typing import Dict, List, Optional

# { pipeline: [upstream_pipelines] }
_dependencies: Dict[str, List[str]] = {}


def add_dependency(pipeline: str, depends_on: str) -> Dict:
    """Register that *pipeline* depends on *depends_on*.

    Returns the current dependency list for *pipeline*.
    Raises ValueError for blank names or self-dependency.
    """
    pipeline = pipeline.strip()
    depends_on = depends_on.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    if not depends_on:
        raise ValueError("depends_on name must not be blank")
    if pipeline == depends_on:
        raise ValueError("a pipeline cannot depend on itself")

    deps = _dependencies.setdefault(pipeline, [])
    if depends_on not in deps:
        deps.append(depends_on)
    return {"pipeline": pipeline, "depends_on": list(deps)}


def remove_dependency(pipeline: str, depends_on: str) -> bool:
    """Remove a single upstream dependency.  Returns True if it existed."""
    deps = _dependencies.get(pipeline, [])
    if depends_on in deps:
        deps.remove(depends_on)
        if not deps:
            del _dependencies[pipeline]
        return True
    return False


def get_dependencies(pipeline: str) -> List[str]:
    """Return the list of upstream pipelines that *pipeline* depends on."""
    return list(_dependencies.get(pipeline, []))


def list_dependencies() -> Dict[str, List[str]]:
    """Return a copy of the full dependency registry."""
    return {k: list(v) for k, v in _dependencies.items()}


def get_blocked_pipelines(unhealthy: List[str]) -> List[str]:
    """Return pipelines whose *direct* upstream dependencies appear in *unhealthy*.

    A pipeline is considered blocked if **any** of its dependencies is unhealthy.
    """
    blocked = []
    for pipeline, deps in _dependencies.items():
        if any(dep in unhealthy for dep in deps):
            blocked.append(pipeline)
    return sorted(blocked)


def clear_dependencies() -> None:  # test helper
    """Remove all registered dependencies."""
    _dependencies.clear()
