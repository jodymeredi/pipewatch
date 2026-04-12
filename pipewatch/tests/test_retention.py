"""Unit tests for pipewatch.retention."""
import datetime
import pytest
import pipewatch.retention as retention


@pytest.fixture(autouse=True)
def reset_registry():
    retention._registry.clear()
    retention._default_policy.update({"max_days": 30, "max_snapshots": 500})
    yield
    retention._registry.clear()
    retention._default_policy.update({"max_days": 30, "max_snapshots": 500})


def test_set_policy_returns_dict():
    result = retention.set_policy("etl_ingest", max_days=7)
    assert result["pipeline"] == "etl_ingest"
    assert result["max_days"] == 7
    assert result["max_snapshots"] is None


def test_set_policy_blank_pipeline_raises():
    with pytest.raises(ValueError, match="blank"):
        retention.set_policy("   ", max_days=7)


def test_set_policy_zero_max_days_raises():
    with pytest.raises(ValueError, match="max_days"):
        retention.set_policy("pipe", max_days=0)


def test_set_policy_negative_max_snapshots_raises():
    with pytest.raises(ValueError, match="max_snapshots"):
        retention.set_policy("pipe", max_snapshots=-1)


def test_get_policy_returns_none_when_missing():
    assert retention.get_policy("nonexistent") is None


def test_get_policy_returns_copy():
    retention.set_policy("pipe", max_days=14)
    p = retention.get_policy("pipe")
    p["max_days"] = 999
    assert retention.get_policy("pipe")["max_days"] == 14


def test_remove_policy_returns_true_when_present():
    retention.set_policy("pipe", max_days=5)
    assert retention.remove_policy("pipe") is True


def test_remove_policy_returns_false_when_absent():
    assert retention.remove_policy("ghost") is False


def test_list_policies_reflects_all_entries():
    retention.set_policy("a", max_days=1)
    retention.set_policy("b", max_days=2)
    names = {p["pipeline"] for p in retention.list_policies()}
    assert names == {"a", "b"}


def test_set_default_policy_updates_defaults():
    retention.set_default_policy(max_days=10, max_snapshots=100)
    assert retention._default_policy["max_days"] == 10
    assert retention._default_policy["max_snapshots"] == 100


def test_resolve_policy_falls_back_to_default():
    policy = retention.resolve_policy("unknown_pipe")
    assert policy["max_days"] == 30


def test_apply_retention_removes_old_snapshots():
    now = datetime.datetime.utcnow()
    old = (now - datetime.timedelta(days=40)).isoformat()
    recent = (now - datetime.timedelta(days=1)).isoformat()
    snapshots = [{"recorded_at": old}, {"recorded_at": recent}]
    retention.set_policy("pipe", max_days=30)
    kept = retention.apply_retention("pipe", snapshots)
    assert len(kept) == 1
    assert kept[0]["recorded_at"] == recent


def test_apply_retention_caps_max_snapshots():
    now = datetime.datetime.utcnow()
    snapshots = [{"recorded_at": (now - datetime.timedelta(minutes=i)).isoformat()} for i in range(10)]
    retention.set_policy("pipe", max_snapshots=3)
    kept = retention.apply_retention("pipe", snapshots)
    assert len(kept) == 3
