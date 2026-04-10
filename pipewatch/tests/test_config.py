"""Tests for pipewatch.config module."""

import textwrap
from pathlib import Path

import pytest

from pipewatch.config import DEFAULT_CONFIG, load_config, validate_config


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------

def test_load_config_returns_defaults_when_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    config = load_config()
    assert config["pipelines"] == []
    assert config["alert"]["notify"] == "log"


def test_load_config_raises_when_explicit_path_missing(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.yaml")


def test_load_config_merges_user_values(tmp_path):
    cfg_file = tmp_path / "pipewatch.yaml"
    cfg_file.write_text(
        textwrap.dedent("""
            check_interval_seconds: 30
            pipelines:
              - name: sales_etl
                source: postgres
            alert:
              max_latency_seconds: 120
        """)
    )
    config = load_config(cfg_file)
    assert config["check_interval_seconds"] == 30
    assert config["pipelines"][0]["name"] == "sales_etl"
    # User override applied
    assert config["alert"]["max_latency_seconds"] == 120
    # Default preserved for keys not overridden
    assert config["alert"]["notify"] == "log"


def test_load_config_uses_env_variable(tmp_path, monkeypatch):
    cfg_file = tmp_path / "custom.yaml"
    cfg_file.write_text("check_interval_seconds: 10\n")
    monkeypatch.setenv("PIPEWATCH_CONFIG", str(cfg_file))
    config = load_config()
    assert config["check_interval_seconds"] == 10


# ---------------------------------------------------------------------------
# validate_config
# ---------------------------------------------------------------------------

def test_validate_config_passes_defaults():
    errors = validate_config(dict(DEFAULT_CONFIG))
    assert errors == []


def test_validate_config_missing_pipeline_name():
    config = {**DEFAULT_CONFIG, "pipelines": [{"source": "s3"}]}
    errors = validate_config(config)
    assert any("missing 'name'" in e for e in errors)


def test_validate_config_invalid_failure_rate():
    config = {
        **DEFAULT_CONFIG,
        "alert": {**DEFAULT_CONFIG["alert"], "max_failure_rate": 1.5},
    }
    errors = validate_config(config)
    assert any("max_failure_rate" in e for e in errors)


def test_validate_config_invalid_latency():
    config = {
        **DEFAULT_CONFIG,
        "alert": {**DEFAULT_CONFIG["alert"], "max_latency_seconds": -1},
    }
    errors = validate_config(config)
    assert any("max_latency_seconds" in e for e in errors)
