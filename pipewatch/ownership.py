"""Pipeline ownership registry — maps pipelines to owner teams/contacts."""

from __future__ import annotations

from typing import Dict, List, Optional

_registry: Dict[str, Dict] = {}


def set_owner(pipeline: str, owner: str, contact: Optional[str] = None, team: Optional[str] = None) -> Dict:
    """Register or update the owner for a pipeline."""
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    owner = owner.strip()
    if not owner:
        raise ValueError("owner must not be blank")

    entry = {"pipeline": pipeline, "owner": owner}
    if contact is not None:
        entry["contact"] = contact.strip()
    if team is not None:
        entry["team"] = team.strip()

    _registry[pipeline] = entry
    return dict(entry)


def get_owner(pipeline: str) -> Optional[Dict]:
    """Return ownership info for *pipeline*, or None if not registered."""
    entry = _registry.get(pipeline.strip())
    return dict(entry) if entry else None


def remove_owner(pipeline: str) -> bool:
    """Remove ownership record for *pipeline*. Returns True if removed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_owners() -> List[Dict]:
    """Return a list of all ownership records."""
    return [dict(v) for v in _registry.values()]


def pipelines_for_owner(owner: str) -> List[str]:
    """Return pipeline names whose owner matches *owner* (case-insensitive)."""
    owner_lower = owner.strip().lower()
    return [
        name
        for name, entry in _registry.items()
        if entry["owner"].lower() == owner_lower
    ]


def pipelines_for_team(team: str) -> List[str]:
    """Return pipeline names belonging to *team* (case-insensitive)."""
    team_lower = team.strip().lower()
    return [
        name
        for name, entry in _registry.items()
        if entry.get("team", "").lower() == team_lower
    ]
