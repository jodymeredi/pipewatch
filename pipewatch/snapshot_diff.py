"""snapshot_diff.py — Compare two pipeline snapshots and surface regressions or recoveries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffEntry:
    pipeline: str
    previous_status: str
    current_status: str
    previous_value: Optional[float]
    current_value: Optional[float]
    changed: bool
    direction: str  # 'regression', 'recovery', 'stable'

    def as_dict(self) -> dict:
        return {
            "pipeline": self.pipeline,
            "previous_status": self.previous_status,
            "current_status": self.current_status,
            "previous_value": self.previous_value,
            "current_value": self.current_value,
            "changed": self.changed,
            "direction": self.direction,
        }


_STATUS_SEVERITY: Dict[str, int] = {
    "ok": 0,
    "warning": 1,
    "critical": 2,
    "unknown": -1,
}


def _severity(status: str) -> int:
    return _STATUS_SEVERITY.get(status.lower(), -1)


def _direction(prev: str, curr: str) -> str:
    ps, cs = _severity(prev), _severity(curr)
    if ps == cs:
        return "stable"
    return "regression" if cs > ps else "recovery"


def diff_snapshots(
    previous: List[dict],
    current: List[dict],
) -> List[DiffEntry]:
    """Return a DiffEntry for every pipeline present in either snapshot list."""
    prev_map: Dict[str, dict] = {m["pipeline"]: m for m in previous}
    curr_map: Dict[str, dict] = {m["pipeline"]: m for m in current}

    all_pipelines = sorted(set(prev_map) | set(curr_map))
    entries: List[DiffEntry] = []

    for pipeline in all_pipelines:
        prev_m = prev_map.get(pipeline)
        curr_m = curr_map.get(pipeline)

        prev_status = prev_m["status"] if prev_m else "unknown"
        curr_status = curr_m["status"] if curr_m else "unknown"
        prev_value = prev_m.get("value") if prev_m else None
        curr_value = curr_m.get("value") if curr_m else None

        changed = prev_status != curr_status
        direction = _direction(prev_status, curr_status)

        entries.append(
            DiffEntry(
                pipeline=pipeline,
                previous_status=prev_status,
                current_status=curr_status,
                previous_value=prev_value,
                current_value=curr_value,
                changed=changed,
                direction=direction,
            )
        )

    return entries


def regressions(entries: List[DiffEntry]) -> List[DiffEntry]:
    return [e for e in entries if e.direction == "regression"]


def recoveries(entries: List[DiffEntry]) -> List[DiffEntry]:
    return [e for e in entries if e.direction == "recovery"]
