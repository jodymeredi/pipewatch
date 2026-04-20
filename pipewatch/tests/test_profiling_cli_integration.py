"""CLI-style integration tests for profiling: simulate how CLI commands would use the API."""

import json
import pytest
from pipewatch import profiling


@pytest.fixture(autouse=True)
def reset():
    profiling._registry.clear()
    yield
    profiling._registry.clear()


def _simulate_record(pipeline: str, duration: float) -> dict:
    profiling.record_duration(pipeline, duration)
    result = profiling.get_profile(pipeline)
    return profiling.as_dict(result)


def _simulate_list() -> list:
    return [profiling.as_dict(r) for r in profiling.profile_all()]


def _simulate_clear(pipeline: str) -> bool:
    return profiling.clear_profile(pipeline)


def test_record_returns_serialisable_dict():
    d = _simulate_record("ingest", 2.0)
    assert json.dumps(d)  # must not raise
    assert d["pipeline"] == "ingest"
    assert d["count"] == 1


def test_list_returns_all_pipelines():
    _simulate_record("pipe_a", 1.0)
    _simulate_record("pipe_b", 3.0)
    results = _simulate_list()
    names = [r["pipeline"] for r in results]
    assert "pipe_a" in names
    assert "pipe_b" in names


def test_clear_removes_pipeline_from_list():
    _simulate_record("pipe_a", 1.0)
    _simulate_clear("pipe_a")
    results = _simulate_list()
    assert all(r["pipeline"] != "pipe_a" for r in results)


def test_record_multiple_then_stats_update():
    for v in [1.0, 2.0, 3.0]:
        _simulate_record("pipe_x", v)
    result = profiling.get_profile("pipe_x")
    assert result.count == 3
    assert result.avg_duration == pytest.approx(2.0)
    assert result.min_duration == 1.0
    assert result.max_duration == 3.0


def test_all_dict_fields_present():
    d = _simulate_record("pipe_z", 0.5)
    for key in ("pipeline", "count", "avg_duration", "min_duration", "max_duration", "p95_duration"):
        assert key in d
