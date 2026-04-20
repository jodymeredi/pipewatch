"""Integration tests: profiling interacts with metrics and evaluate_thresholds."""

import pytest
from pipewatch import profiling
from pipewatch.metrics import collect_metric, evaluate_thresholds


@pytest.fixture(autouse=True)
def reset():
    profiling._registry.clear()
    yield
    profiling._registry.clear()


def _make_metric(pipeline: str, value: float, warn: float = 50.0, crit: float = 90.0):
    return collect_metric(
        pipeline=pipeline,
        value=value,
        warn_threshold=warn,
        crit_threshold=crit,
    )


def test_duration_recorded_per_metric_pipeline():
    metric = _make_metric("etl_load", 30.0)
    profiling.record_duration(metric.pipeline, 1.23)
    result = profiling.get_profile("etl_load")
    assert result is not None
    assert result.count == 1
    assert result.avg_duration == 1.23


def test_multiple_metrics_accumulate_durations():
    for v in [0.5, 1.5, 2.5]:
        m = _make_metric("pipe_x", 20.0)
        profiling.record_duration(m.pipeline, v)
    result = profiling.get_profile("pipe_x")
    assert result.count == 3
    assert result.avg_duration == pytest.approx(1.5)


def test_breaching_pipeline_has_profile_entry():
    metrics = [_make_metric("slow_pipe", 95.0)]
    breaches = evaluate_thresholds(metrics)
    assert any(b.pipeline == "slow_pipe" for b in breaches)
    profiling.record_duration("slow_pipe", 8.7)
    assert profiling.get_profile("slow_pipe") is not None


def test_independent_pipelines_have_independent_profiles():
    profiling.record_duration("pipe_a", 1.0)
    profiling.record_duration("pipe_b", 5.0)
    a = profiling.get_profile("pipe_a")
    b = profiling.get_profile("pipe_b")
    assert a.avg_duration != b.avg_duration
    assert a.pipeline != b.pipeline
