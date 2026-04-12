"""Tests for pipewatch.ownership."""

import pytest

import pipewatch.ownership as ownership


@pytest.fixture(autouse=True)
def reset_registry():
    ownership._registry.clear()
    yield
    ownership._registry.clear()


def test_set_owner_returns_dict():
    result = ownership.set_owner("etl_sales", "alice")
    assert result == {"pipeline": "etl_sales", "owner": "alice"}


def test_set_owner_with_contact_and_team():
    result = ownership.set_owner("etl_sales", "alice", contact="alice@example.com", team="data-eng")
    assert result["contact"] == "alice@example.com"
    assert result["team"] == "data-eng"


def test_set_owner_blank_pipeline_raises():
    with pytest.raises(ValueError, match="pipeline"):
        ownership.set_owner("  ", "alice")


def test_set_owner_blank_owner_raises():
    with pytest.raises(ValueError, match="owner"):
        ownership.set_owner("etl_sales", "   ")


def test_set_owner_overwrites_existing():
    ownership.set_owner("etl_sales", "alice")
    result = ownership.set_owner("etl_sales", "bob", team="platform")
    assert result["owner"] == "bob"
    assert result["team"] == "platform"


def test_get_owner_returns_entry():
    ownership.set_owner("etl_orders", "carol", contact="carol@example.com")
    entry = ownership.get_owner("etl_orders")
    assert entry["owner"] == "carol"
    assert entry["contact"] == "carol@example.com"


def test_get_owner_returns_none_when_missing():
    assert ownership.get_owner("nonexistent") is None


def test_get_owner_returns_copy_not_reference():
    ownership.set_owner("etl_sales", "alice")
    entry = ownership.get_owner("etl_sales")
    entry["owner"] = "hacked"
    assert ownership.get_owner("etl_sales")["owner"] == "alice"


def test_remove_owner_returns_true_when_present():
    ownership.set_owner("etl_sales", "alice")
    assert ownership.remove_owner("etl_sales") is True
    assert ownership.get_owner("etl_sales") is None


def test_remove_owner_returns_false_when_missing():
    assert ownership.remove_owner("ghost") is False


def test_list_owners_reflects_all_entries():
    ownership.set_owner("pipe_a", "alice")
    ownership.set_owner("pipe_b", "bob")
    names = {e["pipeline"] for e in ownership.list_owners()}
    assert names == {"pipe_a", "pipe_b"}


def test_pipelines_for_owner_case_insensitive():
    ownership.set_owner("pipe_a", "Alice")
    ownership.set_owner("pipe_b", "alice")
    ownership.set_owner("pipe_c", "bob")
    result = ownership.pipelines_for_owner("ALICE")
    assert set(result) == {"pipe_a", "pipe_b"}


def test_pipelines_for_team_filters_correctly():
    ownership.set_owner("pipe_a", "alice", team="data-eng")
    ownership.set_owner("pipe_b", "bob", team="platform")
    ownership.set_owner("pipe_c", "carol", team="Data-Eng")
    result = ownership.pipelines_for_team("data-eng")
    assert set(result) == {"pipe_a", "pipe_c"}


def test_pipelines_for_team_empty_when_no_match():
    ownership.set_owner("pipe_a", "alice", team="data-eng")
    assert ownership.pipelines_for_team("unknown-team") == []
