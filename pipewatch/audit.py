"""audit.py — Immutable audit log for pipewatch actions.

Records significant events (config changes, acknowledgments, silences,
baseline updates, etc.) to an append-only in-memory log that can be
persisted to disk for compliance and debugging purposes.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Internal state
# ---------------------------------------------------------------------------

_audit_log: List[Dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utcnow() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _audit_path(directory: str) -> str:
    """Return the path to the audit log file inside *directory*."""
    return os.path.join(directory, "audit.jsonl")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def record_event(
    action: str,
    pipeline: str = "",
    actor: str = "system",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Append an audit event to the in-memory log and return it.

    Args:
        action:   Short label describing what happened, e.g. ``"acknowledge"``.
        pipeline: Name of the affected pipeline (may be empty for global events).
        actor:    Who or what triggered the event (user name, service, etc.).
        details:  Optional free-form mapping with extra context.

    Returns:
        The newly created audit entry as a plain dict.
    """
    if not action or not action.strip():
        raise ValueError("action must be a non-empty string")

    entry: Dict[str, Any] = {
        "timestamp": _utcnow(),
        "action": action.strip(),
        "pipeline": pipeline.strip(),
        "actor": actor.strip() or "system",
        "details": details or {},
    }
    _audit_log.append(entry)
    return entry


def get_events(
    pipeline: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Return recent audit events, optionally filtered.

    Args:
        pipeline: If given, only return events for this pipeline.
        action:   If given, only return events with this action label.
        limit:    Maximum number of events to return (most recent first).

    Returns:
        A list of matching audit entries, newest first.
    """
    results = list(_audit_log)
    if pipeline is not None:
        results = [e for e in results if e["pipeline"] == pipeline.strip()]
    if action is not None:
        results = [e for e in results if e["action"] == action.strip()]
    return list(reversed(results))[:limit]


def clear_events() -> None:
    """Wipe the in-memory audit log (primarily for testing)."""
    _audit_log.clear()


def flush_to_disk(directory: str) -> str:
    """Append all in-memory events to a JSONL file on disk.

    Each line in the file is a JSON-encoded audit entry.  Existing content
    is preserved; new entries are appended.

    Args:
        directory: Directory where ``audit.jsonl`` will be written.

    Returns:
        The absolute path of the audit log file.
    """
    os.makedirs(directory, exist_ok=True)
    path = _audit_path(directory)
    with open(path, "a", encoding="utf-8") as fh:
        for entry in _audit_log:
            fh.write(json.dumps(entry) + "\n")
    return path


def load_from_disk(directory: str) -> List[Dict[str, Any]]:
    """Read all audit events from the on-disk JSONL file.

    Args:
        directory: Directory containing ``audit.jsonl``.

    Returns:
        A list of audit entries in chronological order.  Returns an empty
        list if the file does not exist.
    """
    path = _audit_path(directory)
    if not os.path.exists(path):
        return []
    entries: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # skip malformed lines
    return entries
