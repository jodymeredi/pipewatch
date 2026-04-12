"""Edge-case tests for pipewatch.retention."""
import datetime
import pytest
import pipewatch.retention as retention


@pytest.fixture(autouse=True)
def reset():
    retention._registry.clear()
    retention._default_policy.update({"max_days": 30, "max_snapshots": 500})
    yield
    retention._registry.clear()


def test_overwrite_policy_updates_values():
    retention.set_policy("pipe", max_days=5)
    retention.set_policy("pipe", max_days=90, max_snapshots=200)
    p = retention.get_policy("pipe")
    assert p["max_days"] == 90
    assert p["max_snapshots"] == 200


def test_apply_retention_empty_list_returns_empty():
    retention.set_policy("pipe", max_days=7)
    assert retention.apply_retention("pipe", []) == []


def test_apply_retention_all_within_window_kept():
    now = datetime.datetime.utcnow()
    snapshots = [
        {"recorded_at": (now - datetime.timedelta(days=1)).isoformat()},
        {"recorded_at": (now - datetime.timedelta(hours=1)).isoformat()},
    ]
    retention.set_policy("pipe", max_days=30, max_snapshots=100)
    kept = retention.apply_retention("pipe", snapshots)
    assert len(kept) == 2


def test_set_default_policy_zero_raises():
    with pytest.raises(ValueError):
        retention.set_default_policy(max_days=0)


def test_set_default_policy_negative_snapshots_raises():
    with pytest.raises(ValueError):
        retention.set_default_policy(max_days=7, max_snapshots=-5)


def test_list_policies_returns_copies():
    retention.set_policy("pipe", max_days=10)
    policies = retention.list_policies()
    policies[0]["max_days"] = 999
    assert retention.get_policy("pipe")["max_days"] == 10


def test_resolve_policy_returns_specific_over_default():
    retention.set_default_policy(max_days=30, max_snapshots=500)
    retention.set_policy("pipe", max_days=7, max_snapshots=50)
    p = retention.resolve_policy("pipe")
    assert p["max_days"] == 7
    assert p["max_snapshots"] == 50
