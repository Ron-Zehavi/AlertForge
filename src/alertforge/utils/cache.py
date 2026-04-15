"""File-based cache for raw API responses and processed data."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def cache_path(data_dir: Path, namespace: str, key: str, ext: str = "json") -> Path:
    """Build a cache file path: {data_dir}/{namespace}/{key}.{ext}."""
    safe_key = _sanitize_key(key)
    return data_dir / namespace / f"{safe_key}.{ext}"


def is_cached(
    data_dir: Path, namespace: str, key: str, ext: str = "json", ttl_days: int = 30
) -> bool:
    """Check if a cached file exists and is within TTL."""
    path = cache_path(data_dir, namespace, key, ext)
    if not path.exists():
        return False
    age_days = (time.time() - path.stat().st_mtime) / 86400
    return age_days < ttl_days


def read_json(data_dir: Path, namespace: str, key: str) -> Any:
    """Read a cached JSON file."""
    path = cache_path(data_dir, namespace, key, "json")
    with open(path) as f:
        return json.load(f)


def write_json(data_dir: Path, namespace: str, key: str, data: Any) -> Path:
    """Write data to a cached JSON file."""
    path = cache_path(data_dir, namespace, key, "json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    logger.debug("Cached %s/%s", namespace, key)
    return path


def read_text(data_dir: Path, namespace: str, key: str, ext: str = "csv") -> str:
    """Read a cached text file."""
    path = cache_path(data_dir, namespace, key, ext)
    return path.read_text()


def write_text(data_dir: Path, namespace: str, key: str, content: str, ext: str = "csv") -> Path:
    """Write text content to a cached file."""
    path = cache_path(data_dir, namespace, key, ext)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    logger.debug("Cached %s/%s.%s", namespace, key, ext)
    return path


def _sanitize_key(key: str) -> str:
    """Sanitize a cache key to prevent path traversal.

    Strips path separators and validates the key contains only
    safe characters (alphanumeric, dash, underscore, dot).
    """
    safe = key.replace("/", "_").replace("\\", "_").replace("..", "_")
    if not safe or safe != key.strip():
        msg = f"Invalid cache key: {key!r}"
        raise ValueError(msg)
    return safe
