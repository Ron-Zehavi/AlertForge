"""Tests for application configuration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from alertforge.config import AppConfig, load_config, reset_config_cache

if TYPE_CHECKING:
    pass


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    reset_config_cache()


def test_load_default_config() -> None:
    config = load_config()
    assert config.api.port == 8000
    assert config.data.raw_dir == Path("data/raw")


def test_load_config_from_yaml(tmp_path: Path) -> None:
    yaml_content = """
api:
  host: "127.0.0.1"
  port: 9000
data:
  raw_dir: "/tmp/raw"
brokers:
  fink:
    base_url: "https://fink-portal.org"
    rate_limit_rps: 5.0
cache:
  enabled: false
  ttl_days: 7
"""
    config_file = tmp_path / "test_config.yaml"
    config_file.write_text(yaml_content)

    config = load_config(config_file)

    assert config.api.host == "127.0.0.1"
    assert config.api.port == 9000
    assert config.data.raw_dir == Path("/tmp/raw")
    assert config.brokers["fink"].base_url == "https://fink-portal.org"
    assert config.brokers["fink"].rate_limit_rps == 5.0
    assert config.cache.enabled is False
    assert config.cache.ttl_days == 7


def test_load_missing_config_uses_defaults(tmp_path: Path) -> None:
    config = load_config(tmp_path / "nonexistent.yaml")
    assert config.api.port == 8000
    assert config.brokers == {}


def test_broker_config_defaults() -> None:
    config = AppConfig.model_validate({"brokers": {"test": {"base_url": "https://example.com"}}})
    assert config.brokers["test"].rate_limit_rps == 1.0
    assert config.brokers["test"].timeout_s == 30.0


def test_tns_token_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TNS_BOT_TOKEN", "test-token-123")
    config = AppConfig.model_validate({})
    assert config.tns_bot_token == "test-token-123"


def test_require_tns_token_raises_when_missing() -> None:
    config = AppConfig.model_validate({})
    with pytest.raises(ValueError, match="TNS_BOT_TOKEN is required"):
        config.require_tns_token()


def test_require_tns_token_returns_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TNS_BOT_TOKEN", "my-token")
    config = AppConfig.model_validate({})
    assert config.require_tns_token() == "my-token"


def test_config_caching() -> None:
    config1 = load_config()
    config2 = load_config()
    assert config1 is config2
