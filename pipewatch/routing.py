"""Alert routing: direct pipeline alerts to specific notification channels."""

from __future__ import annotations

from typing import Dict, List, Optional

# registry: pipeline_name -> list of channel names
_routes: Dict[str, List[str]] = {}
_default_channels: List[str] = []


def set_route(pipeline: str, channels: List[str]) -> Dict:
    """Assign one or more channels to a pipeline. Replaces any existing route."""
    if not pipeline or not pipeline.strip():
        raise ValueError("pipeline name must be a non-empty string")
    if not channels:
        raise ValueError("channels list must not be empty")
    cleaned = [c for c in channels if c and c.strip()]
    if not cleaned:
        raise ValueError("channels list contains no valid entries")
    _routes[pipeline] = cleaned
    return {"pipeline": pipeline, "channels": cleaned}


def get_route(pipeline: str) -> List[str]:
    """Return channels for a pipeline, falling back to defaults."""
    return list(_routes.get(pipeline, _default_channels))


def remove_route(pipeline: str) -> bool:
    """Remove routing rule for a pipeline. Returns True if it existed."""
    if pipeline in _routes:
        del _routes[pipeline]
        return True
    return False


def set_default_channels(channels: List[str]) -> None:
    """Set fallback channels used when no specific route matches."""
    global _default_channels
    if not channels:
        raise ValueError("default channels list must not be empty")
    _default_channels = list(channels)


def list_routes() -> List[Dict]:
    """Return all explicit routing rules."""
    return [{"pipeline": p, "channels": list(ch)} for p, ch in _routes.items()]


def resolve_channels(pipeline: str) -> List[str]:
    """Return the effective channel list for a pipeline (explicit or default)."""
    return get_route(pipeline)


def clear_routes() -> None:
    """Remove all routing rules and reset default channels (testing helper)."""
    global _default_channels
    _routes.clear()
    _default_channels = []
