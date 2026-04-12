"""Integration tests: retention interacts with history snapshots."""
import datetime
import json
import pathlib
import pytest
import pipewatch.retention as retention
import pipewatch.history as history


@pytest.fixture()
def hist_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(history, "_history_path", lambda: tmp_path / "history.jsonl")
    return tmp_path


@pytest.fixture(autouse=True)
def reset(hist_dir):
    retention._registry.clear()
    retention._default_policy.update({"max_days": 30, "max_snapshots": 500})
    yield
    retention._registry.clear()


def _make_snapshot(pipeline: str, days_ago: int) -> dict:
    ts = (datetime.datetime.utcnow() - datetime.timedelta(days=days_ago)).isoformat()
    return {
        "pipeline": pipeline,
        "value": 1.0,
        "status": "ok",
        "recorded_at": ts,
    }


def test_apply_retention_on_loaded_snapshots(hist_dir):
    path = history._history_path()
    entries = [
        _make_snapshot("pipe_a", days_ago=50),
        _make_snapshot("pipe_a", days_ago=10),
        _make_snapshot("pipe_a", days_ago=1),
    ]
    with path.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    snapshots = history.load_snapshots("pipe_a")
    retention.set_policy("pipe_a", max_days=30)
    kept = retention.apply_retention("pipe_a", snapshots)
    assert len(kept) == 2


def test_no_policy_uses_default_max_days(hist_dir):
    retention.set_default_policy(max_days=7, max_snapshots=500)
    path = history._history_path()
    entries = [
        _make_snapshot("pipe_b", days_ago=8),
        _make_snapshot("pipe_b", days_ago=3),
    ]
    with path.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    snapshots = history.load_snapshots("pipe_b")
    kept = retention.apply_retention("pipe_b", snapshots)
    assert len(kept) == 1
    assert kept[0]["recorded_at"] == entries[1]["recorded_at"]


def test_max_snapshots_trims_oldest(hist_dir):
    path = history._history_path()
    entries = [
        _make_snapshot("pipe_c", days_ago=i) for i in range(5, 0, -1)
    ]
    with path.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    snapshots = history.load_snapshots("pipe_c")
    retention.set_policy("pipe_c", max_snapshots=2)
    kept = retention.apply_retention("pipe_c", snapshots)
    assert len(kept) == 2
