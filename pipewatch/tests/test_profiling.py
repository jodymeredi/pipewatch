"""Unit tests for pipewatch.profiling."""

import pytest
from pipewatch import profiling


@pytest.fixture(autouse=True)
def reset_registry():
    profiling._registry.clear()
    yield
    profiling._registry.clear()


def test_record_duration_stores_sample():
    profiling.record_duration("pipe_a", 1.5)
    assert "pipe_a" in profiling._registry
    assert profiling._registry["pipe_a"] == [1.5]


def test_record_duration_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        profiling.record_duration("  ", 1.0)


def test_record_duration_negative_raises():
    with pytest.raises(ValueError, match="non-negative"):
        profiling.record_duration("pipe_a", -0.1)


def test_record_duration_accumulates_samples():
    for v in [1.0, 2.0, 3.0]:
        profiling.record_duration("pipe_a", v)
    assert len(profiling._registry["pipe_a"]) == 3


def test_record_duration_caps_at_max_samples():
    profiling._max_samples = 5
    for i in range(10):
        profiling.record_duration("pipe_a", float(i))
    assert len(profiling._registry["pipe_a"]) == 5
    profiling._max_samples = 100


def test_get_profile_returns_none_when_no_data():
    assert profiling.get_profile("missing") is None


def test_get_profile_returns_result():
    for v in [1.0, 2.0, 3.0, 4.0, 5.0]:
        profiling.record_duration("pipe_a", v)
    result = profiling.get_profile("pipe_a")
    assert result is not None
    assert result.pipeline == "pipe_a"
    assert result.count == 5
    assert result.min_duration == 1.0
    assert result.max_duration == 5.0
    assert result.avg_duration == 3.0


def test_get_profile_p95():
    for i in range(1, 21):
        profiling.record_duration("pipe_a", float(i))
    result = profiling.get_profile("pipe_a")
    assert result is not None
    assert result.p95_duration is not None
    assert result.p95_duration <= 20.0


def test_as_dict_serialisable():
    import json
    profiling.record_duration("pipe_a", 2.5)
    result = profiling.get_profile("pipe_a")
    d = profiling.as_dict(result)
    assert json.dumps(d)  # should not raise
    assert d["pipeline"] == "pipe_a"


def test_clear_profile_returns_true_when_present():
    profiling.record_duration("pipe_a", 1.0)
    assert profiling.clear_profile("pipe_a") is True
    assert "pipe_a" not in profiling._registry


def test_clear_profile_returns_false_when_absent():
    assert profiling.clear_profile("ghost") is False


def test_list_profiles_reflects_recorded_pipelines():
    profiling.record_duration("pipe_a", 1.0)
    profiling.record_duration("pipe_b", 2.0)
    names = profiling.list_profiles()
    assert "pipe_a" in names
    assert "pipe_b" in names


def test_profile_all_returns_results_for_all():
    profiling.record_duration("pipe_a", 1.0)
    profiling.record_duration("pipe_b", 2.0)
    results = profiling.profile_all()
    pipelines = {r.pipeline for r in results}
    assert {"pipe_a", "pipe_b"} == pipelines
