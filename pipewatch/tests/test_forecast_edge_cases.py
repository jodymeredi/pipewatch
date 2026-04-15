"""Edge-case tests for pipewatch.forecast."""
import json
import os
import tempfile
from datetime import datetime, timezone

import pytest

from pipewatch.forecast import forecast_pipeline, as_dict, ForecastResult


def _write(directory: str, rows: list[dict]):
    path = os.path.join(directory, "snap.jsonl")
    with open(path, "w") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def _snap(pipeline, name, value):
    return {
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "metrics": [{"pipeline": pipeline, "name": name, "value": value, "status": "ok"}],
    }


def test_forecast_empty_history_returns_none():
    with tempfile.TemporaryDirectory() as d:
        result = forecast_pipeline("p", "v", history_dir=d)
    assert result is None


def test_forecast_constant_series_slope_zero():
    with tempfile.TemporaryDirectory() as d:
        _write(d, [_snap("p", "v", 7.0) for _ in range(5)])
        result = forecast_pipeline("p", "v", history_dir=d)
    assert result is not None
    assert result.slope == pytest.approx(0.0)
    assert result.predicted_value == pytest.approx(7.0)


def test_forecast_horizon_zero_predicts_last_step():
    """horizon=0 should predict at the last observed index."""
    with tempfile.TemporaryDirectory() as d:
        _write(d, [_snap("p", "v", float(i)) for i in range(5)])
        result = forecast_pipeline("p", "v", horizon=0, history_dir=d)
    assert result is not None
    # slope=1, intercept=0, predict at index 4+0=4
    assert result.predicted_value == pytest.approx(4.0)


def test_forecast_missing_value_key_skipped():
    """Entries without 'value' should be silently skipped."""
    with tempfile.TemporaryDirectory() as d:
        rows = [_snap("p", "v", float(i)) for i in range(4)]
        # inject a broken entry
        rows.insert(2, {
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "metrics": [{"pipeline": "p", "name": "v"}],  # no value key
        })
        _write(d, rows)
        result = forecast_pipeline("p", "v", history_dir=d)
    assert result is not None
    assert result.data_points == 4


def test_as_dict_rounds_predicted_value():
    r = ForecastResult(
        pipeline="p", metric_name="m", horizon=1,
        predicted_value=3.14159265,
        slope=0.000012345,
        intercept=1.23456789,
        confidence="low",
        data_points=3,
    )
    d = as_dict(r)
    assert d["predicted_value"] == round(3.14159265, 4)
    assert d["slope"] == round(0.000012345, 6)


def test_forecast_large_horizon():
    """Forecasting far ahead should not crash."""
    with tempfile.TemporaryDirectory() as d:
        _write(d, [_snap("p", "v", float(i)) for i in range(10)])
        result = forecast_pipeline("p", "v", horizon=1000, history_dir=d)
    assert result is not None
    assert result.predicted_value > 0
