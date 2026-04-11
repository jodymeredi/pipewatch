"""CLI-level integration: baseline subcommand wiring (simulated)."""

import json
import pytest

import pipewatch.baseline as bl


@pytest.fixture(autouse=True)
def reset():
    bl.clear_baselines()
    yield
    bl.clear_baselines()


def _simulate_set(pipeline, metric, value):
    """Simulate `pipewatch baseline set <pipeline> <metric> <value>`."""
    return bl.set_baseline(pipeline, metric, float(value))


def _simulate_get(pipeline, metric):
    """Simulate `pipewatch baseline get <pipeline> <metric>`."""
    v = bl.get_baseline(pipeline, metric)
    return {"pipeline": pipeline, "metric": metric, "baseline": v}


def _simulate_list():
    """Simulate `pipewatch baseline list`."""
    return bl.list_baselines()


def _simulate_remove(pipeline, metric):
    """Simulate `pipewatch baseline remove <pipeline> <metric>`."""
    return bl.remove_baseline(pipeline, metric)


def test_set_then_get_roundtrip():
    _simulate_set("sales_etl", "rows", 2000)
    result = _simulate_get("sales_etl", "rows")
    assert result["baseline"] == 2000.0


def test_list_after_multiple_sets():
    _simulate_set("a", "rows", 100)
    _simulate_set("a", "latency", 0.5)
    _simulate_set("b", "rows", 50)
    listing = _simulate_list()
    assert set(listing.keys()) == {"a", "b"}
    assert listing["a"]["rows"] == 100.0
    assert listing["a"]["latency"] == 0.5


def test_remove_then_list_reflects_deletion():
    _simulate_set("pipe", "rows", 10)
    _simulate_remove("pipe", "rows")
    listing = _simulate_list()
    assert "pipe" not in listing


def test_set_output_is_json_serialisable():
    result = _simulate_set("pipe", "rows", 42)
    dumped = json.dumps(result)
    loaded = json.loads(dumped)
    assert loaded["baseline"] == 42.0


def test_compare_output_is_json_serialisable():
    bl.set_baseline("pipe", "rows", 100.0)
    result = bl.compare_to_baseline("pipe", "rows", 115.0)
    dumped = json.dumps(result)
    loaded = json.loads(dumped)
    assert loaded["breached"] is True


def test_persist_and_reload_across_sessions(tmp_path):
    _simulate_set("session_pipe", "rows", 777)
    bl.save_baselines(str(tmp_path))
    bl.clear_baselines()
    assert bl.get_baseline("session_pipe", "rows") is None
    bl.load_baselines(str(tmp_path))
    assert bl.get_baseline("session_pipe", "rows") == 777.0
