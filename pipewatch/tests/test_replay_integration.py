"""Integration tests: replay_snapshots wired to real history + evaluate_thresholds."""

from __future__ import annotations

import json
import os

import pytest

from pipewatch.history import record_snapshot
from pipewatch.metrics import PipelineMetric
from pipewatch.replay import replay_snapshots, summarize_replay


@pytest.fixture()
def hist_dir(tmp_path):
    return str(tmp_path)


def _make_metric(pipeline: str, value: float) -> PipelineMetric:
    return PipelineMetric(pipeline=pipeline, value=value, unit="rows", tags={})


def test_replay_over_recorded_history(hist_dir):
    """Snapshots written via record_snapshot are picked up by replay_snapshots."""
    metrics = [_make_metric("etl_load", 42.0), _make_metric("etl_extract", 7.0)]
    record_snapshot(metrics, history_dir=hist_dir)

    results = replay_snapshots(hist_dir, dry_run=True)
    assert len(results) == 2
    pipelines = {r.pipeline for r in results}
    assert pipelines == {"etl_load", "etl_extract"}


def test_replay_multiple_snapshots_all_processed(hist_dir):
    """Multiple calls to record_snapshot produce multiple replay entries."""
    for val in [10.0, 20.0, 30.0]:
        record_snapshot([_make_metric("pipe_a", val)], history_dir=hist_dir)

    results = replay_snapshots(hist_dir, pipeline="pipe_a", dry_run=True)
    assert len(results) == 3
    assert all(r.pipeline == "pipe_a" for r in results)


def test_summarize_after_replay_is_consistent(hist_dir):
    record_snapshot([_make_metric("p1", 1.0), _make_metric("p2", 2.0)], history_dir=hist_dir)
    results = replay_snapshots(hist_dir, dry_run=True)
    summary = summarize_replay(results)
    assert summary["total"] == len(results)
    assert summary["ok"] + summary["breaching"] == summary["total"]
