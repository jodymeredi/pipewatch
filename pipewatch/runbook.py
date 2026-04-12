"""runbook.py – associate runbook URLs / notes with pipelines for alert context."""

from __future__ import annotations

from typing import Dict, List, Optional

# { pipeline_name: {"url": str, "notes": str} }
_registry: Dict[str, Dict[str, str]] = {}


def set_runbook(
    pipeline: str,
    url: str = "",
    notes: str = "",
) -> Dict[str, str]:
    """Attach a runbook URL and/or notes to *pipeline*.

    At least one of *url* or *notes* must be non-empty.
    """
    pipeline = pipeline.strip()
    if not pipeline:
        raise ValueError("pipeline name must not be blank")
    url = url.strip()
    notes = notes.strip()
    if not url and not notes:
        raise ValueError("at least one of url or notes must be provided")
    entry: Dict[str, str] = {"pipeline": pipeline, "url": url, "notes": notes}
    _registry[pipeline] = entry
    return dict(entry)


def get_runbook(pipeline: str) -> Optional[Dict[str, str]]:
    """Return the runbook entry for *pipeline*, or ``None`` if not set."""
    entry = _registry.get(pipeline.strip())
    return dict(entry) if entry else None


def remove_runbook(pipeline: str) -> bool:
    """Remove the runbook entry for *pipeline*. Returns ``True`` if it existed."""
    return _registry.pop(pipeline.strip(), None) is not None


def list_runbooks() -> List[Dict[str, str]]:
    """Return a list of all runbook entries (copies)."""
    return [dict(v) for v in _registry.values()]


def enrich_alert(pipeline: str, alert_dict: Dict) -> Dict:
    """Attach runbook info to *alert_dict* in-place and return it.

    If no runbook is registered the dict is returned unchanged.
    """
    entry = get_runbook(pipeline)
    if entry:
        alert_dict["runbook_url"] = entry["url"]
        alert_dict["runbook_notes"] = entry["notes"]
    return alert_dict
