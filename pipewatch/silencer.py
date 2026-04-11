"""Alert silencing / mute rules for pipewatch.

Allows operators to suppress alerts for a pipeline+status combination
during a defined time window (e.g. during planned maintenance).
"""

from __future__ import annotations

import fnmatch
from datetime import datetime, timezone
from typing import Dict, List, Optional

# In-memory registry: list of active silence rules
_SILENCE_RULES: List[Dict] = []


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def add_silence(
    pipeline_pattern: str,
    reason: str,
    expires_at: Optional[datetime] = None,
    statuses: Optional[List[str]] = None,
) -> Dict:
    """Register a new silence rule.

    Args:
        pipeline_pattern: Glob pattern matched against pipeline names.
        reason: Human-readable reason for the silence.
        expires_at: UTC datetime when the rule expires. None = never.
        statuses: List of status strings to silence (e.g. ['warning']).
                  None means silence all statuses.

    Returns:
        The created rule dict.
    """
    rule = {
        "pipeline_pattern": pipeline_pattern,
        "reason": reason,
        "expires_at": expires_at,
        "statuses": [s.lower() for s in statuses] if statuses else None,
        "created_at": _utcnow(),
    }
    _SILENCE_RULES.append(rule)
    return rule


def remove_expired_silences(now: Optional[datetime] = None) -> int:
    """Purge rules whose expiry has passed. Returns number removed."""
    global _SILENCE_RULES
    now = now or _utcnow()
    before = len(_SILENCE_RULES)
    _SILENCE_RULES = [
        r for r in _SILENCE_RULES
        if r["expires_at"] is None or r["expires_at"] > now
    ]
    return before - len(_SILENCE_RULES)


def is_silenced(pipeline_name: str, status: str, now: Optional[datetime] = None) -> bool:
    """Return True if the pipeline+status combination is currently silenced."""
    now = now or _utcnow()
    status_lower = status.lower()
    for rule in _SILENCE_RULES:
        if rule["expires_at"] is not None and rule["expires_at"] <= now:
            continue
        if not fnmatch.fnmatch(pipeline_name, rule["pipeline_pattern"]):
            continue
        if rule["statuses"] is None or status_lower in rule["statuses"]:
            return True
    return False


def list_silences() -> List[Dict]:
    """Return a shallow copy of all active silence rules."""
    return list(_SILENCE_RULES)


def clear_all_silences() -> None:
    """Remove every silence rule (useful in tests)."""
    _SILENCE_RULES.clear()
