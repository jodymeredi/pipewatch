"""CLI-style integration tests for retention policy helpers."""
import pytest
import pipewatch.retention as retention


@pytest.fixture(autouse=True)
def reset():
    retention._registry.clear()
    retention._default_policy.update({"max_days": 30, "max_snapshots": 500})
    yield
    retention._registry.clear()


def _simulate_set(pipeline, max_days=None, max_snapshots=None):
    return retention.set_policy(pipeline, max_days=max_days, max_snapshots=max_snapshots)


def _simulate_get(pipeline):
    return retention.get_policy(pipeline)


def _simulate_list():
    return retention.list_policies()


def _simulate_remove(pipeline):
    return retention.remove_policy(pipeline)


def test_set_returns_correct_dict():
    r = _simulate_set("pipe_x", max_days=14, max_snapshots=250)
    assert r == {"pipeline": "pipe_x", "max_days": 14, "max_snapshots": 250}


def test_get_after_set_returns_policy():
    _simulate_set("pipe_y", max_days=3)
    r = _simulate_get("pipe_y")
    assert r["max_days"] == 3


def test_list_after_multiple_sets():
    _simulate_set("a", max_days=1)
    _simulate_set("b", max_days=2)
    _simulate_set("c", max_days=3)
    results = _simulate_list()
    assert len(results) == 3
    names = {r["pipeline"] for r in results}
    assert names == {"a", "b", "c"}


def test_remove_then_get_returns_none():
    _simulate_set("pipe_z", max_days=7)
    _simulate_remove("pipe_z")
    assert _simulate_get("pipe_z") is None


def test_remove_nonexistent_returns_false():
    assert _simulate_remove("does_not_exist") is False


def test_set_only_max_snapshots():
    r = _simulate_set("pipe_snap", max_snapshots=100)
    assert r["max_days"] is None
    assert r["max_snapshots"] == 100
