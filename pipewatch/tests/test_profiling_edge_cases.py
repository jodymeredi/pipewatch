"""Edge case tests for pipewatch.profiling."""

import pytest
from pipewatch import profiling


@pytest.fixture(autouse=True)
def reset_registry():
    profiling._registry.clear()
    yield
    profiling._registry.clear()


def test_record_zero_duration_accepted():
    profiling.record_duration("pipe_a", 0.0)
    result = profiling.get_profile("pipe_a")
    assert result is not None
    assert result.min_duration == 0.0


def test_single_sample_p95_equals_that_sample():
    profiling.record_duration("pipe_a", 3.14)
    result = profiling.get_profile("pipe_a")
    assert result.p95_duration == 3.14
    assert result.min_duration == 3.14
    assert result.max_duration == 3.14


def test_pipeline_name_stripped_on_record():
    profiling.record_duration("  pipe_a  ", 1.0)
    assert "pipe_a" in profiling._registry
    assert "  pipe_a  " not in profiling._registry


def test_pipeline_name_stripped_on_get():
    profiling.record_duration("pipe_a", 1.0)
    result = profiling.get_profile("  pipe_a  ")
    assert result is not None
    assert result.pipeline == "pipe_a"


def test_profile_all_empty_registry_returns_empty_list():
    assert profiling.profile_all() == []


def test_clear_then_rerecord():
    profiling.record_duration("pipe_a", 1.0)
    profiling.clear_profile("pipe_a")
    profiling.record_duration("pipe_a", 9.0)
    result = profiling.get_profile("pipe_a")
    assert result.count == 1
    assert result.avg_duration == 9.0


def test_large_sample_set_avg_correct():
    values = [float(i) for i in range(1, 101)]
    for v in values:
        profiling.record_duration("pipe_a", v)
    result = profiling.get_profile("pipe_a")
    assert result is not None
    assert result.avg_duration == pytest.approx(50.5, rel=1e-3)
