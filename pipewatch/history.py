"""Persist and retrieve pipeline metric snapshots for trend analysis."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

DEFAULT_HISTORY_DIR = Path.home() / ".pipewatch" / "history"


def _history_path(pipeline_name: str, history_dir: Path) -> Path:
    """Return the JSON-lines file path for a given pipeline."""
    safe_name = pipeline_name.replace(os.sep, "_").replace(" ", "_")
    return history_dir / f"{safe_name}.jsonl"


def record_snapshot(
    pipeline_name: str,
    metric_dict: dict,
    history_dir: Optional[Path] = None,
) -> Path:
    """Append a timestamped metric snapshot to the pipeline history file.

    Returns the path of the history file written to.
    """
    history_dir = Path(history_dir) if history_dir else DEFAULT_HISTORY_DIR
    history_dir.mkdir(parents=True, exist_ok=True)

    path = _history_path(pipeline_name, history_dir)
    entry = {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        **metric_dict,
    }
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return path


def load_snapshots(
    pipeline_name: str,
    history_dir: Optional[Path] = None,
    limit: int = 100,
) -> List[dict]:
    """Return the most recent *limit* snapshots for a pipeline.

    Returns an empty list when no history file exists.
    """
    history_dir = Path(history_dir) if history_dir else DEFAULT_HISTORY_DIR
    path = _history_path(pipeline_name, history_dir)

    if not path.exists():
        return []

    entries: List[dict] = []
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue

    return entries[-limit:]


def purge_history(pipeline_name: str, history_dir: Optional[Path] = None) -> bool:
    """Delete the history file for a pipeline.  Returns True if file existed."""
    history_dir = Path(history_dir) if history_dir else DEFAULT_HISTORY_DIR
    path = _history_path(pipeline_name, history_dir)
    if path.exists():
        path.unlink()
        return True
    return False
