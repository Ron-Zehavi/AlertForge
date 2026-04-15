"""Application configuration loaded from YAML + environment variables."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, model_validator


class BrokerConfig(BaseModel):
    """Configuration for a single broker API."""

    base_url: str
    rate_limit_rps: float = 1.0
    timeout_s: float = 30.0


class DataConfig(BaseModel):
    """Paths for data storage."""

    raw_dir: Path = Path("data/raw")
    processed_dir: Path = Path("data/processed")
    models_dir: Path = Path("data/models")


class CacheConfig(BaseModel):
    """Cache settings."""

    enabled: bool = True
    ttl_days: int = 30


class ApiConfig(BaseModel):
    """API server settings."""

    host: str = "0.0.0.0"
    port: int = 8000


class AppConfig(BaseModel):
    """Root application configuration."""

    api: ApiConfig = ApiConfig()
    data: DataConfig = DataConfig()
    brokers: dict[str, BrokerConfig] = {}
    cache: CacheConfig = CacheConfig()
    tns_bot_token: str = ""

    @model_validator(mode="before")
    @classmethod
    def _load_tns_token_from_env(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Load TNS bot token from environment if not set in config."""
        import os

        if not values.get("tns_bot_token"):
            values["tns_bot_token"] = os.environ.get("TNS_BOT_TOKEN", "")
        return values

    def require_tns_token(self) -> str:
        """Return TNS bot token or raise if missing."""
        if not self.tns_bot_token:
            msg = (
                "TNS_BOT_TOKEN is required for TNS ingestion. "
                "Set it in .env or as an environment variable. "
                "Register a bot at https://www.wis-tns.org/bots"
            )
            raise ValueError(msg)
        return self.tns_bot_token


_CONFIG_PATH = Path("configs/config.yaml")
_cached_config: AppConfig | None = None


def load_config(path: Path | None = None) -> AppConfig:
    """Load configuration from YAML file.

    Results are cached after first load. Pass a path to override
    the default location (useful for testing).
    """
    global _cached_config  # noqa: PLW0603

    if _cached_config is not None and path is None:
        return _cached_config

    config_path = path or _CONFIG_PATH
    if config_path.exists():
        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}
    else:
        raw = {}

    config = AppConfig.model_validate(raw)

    if path is None:
        _cached_config = config

    return config


def reset_config_cache() -> None:
    """Clear the cached config (for testing)."""
    global _cached_config  # noqa: PLW0603
    _cached_config = None
