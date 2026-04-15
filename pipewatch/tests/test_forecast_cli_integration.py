"""CLI-style integration: simulate how forecast results feed into reporting."""
import json
import os
import tempfile

import pytest

from pipewatch.forecast import forecast_pipeline, forecast_bulk, as_dict
from pipewatch.history import record_snapshot
from pipewatch.metrics import PipelineMetric


def _m(pipeline: str, value: float) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, name="latency", value=value, status="ok", tags={})


def test_forecast_result_fields_complete():
    with tempfile.TemporaryDirectory() as d:
        for i in range(6):
            record_snapshot([_m("svc", float(i))], history_dir=d)
        result = forecast_pipeline("svc", "latency", horizon=1, history_dir=d)
    assert result is not None
    d_ = as_dict(result)
    for key in ("pipeline", "metric_name", "horizon", "predicted_value",
                "slope", "intercept", "confidence", "data_points"):
        assert key in d_


def test_forecast_result_as_dict_json_serialisable():
    with tempfile.TemporaryDirectory() as d:
        for i in range(6):
            record_snapshot([_m("svc", float(i * 3))], history_dir=d)
        result = forecast_pipeline("svc", "latency", history_dir=d)
    assert result is not None
    payload = json.dumps(as_dict(result))
    parsed = json.loads(payload)
    assert parsed["pipeline"] == "svc"


def test_bulk_forecast_all_serialisable():
    with tempfile.TemporaryDirectory() as d:
        for i in range(5):
            record_snapshot([
                _m("alpha", float(i)),
                _m("beta", float(i * 2)),
            ], history_dir=d)
        results = forecast_bulk(["alpha", "beta"], "latency", history_dir=d)
    assert len(results) == 2
    for r in results:
        json.dumps(as_dict(r))  # must not raise


def test_forecast_confidence_grows_with_more_data():
    with tempfile.TemporaryDirectory() as d:
        # 4 snapshots → low confidence
        for i in range(4):
            record_snapshot([_m("p", float(i))], history_dir=d)
        r_low = forecast_pipeline("p", "latency", history_dir=d)

    with tempfile.TemporaryDirectory() as d:
        # 25 snapshots → high confidence
        for i in range(25):
            record_snapshot([_m("p", float(i))], history_dir=d)
        r_high = forecast_pipeline("p", "latency", history_dir=d)

    assert r_low is not None and r_high is not None
    assert r_low.confidence == "low"
    assert r_high.confidence == "high"
