"""Tests for file-based cache."""

from __future__ import annotations

from pathlib import Path

import pytest

from alertforge.utils.cache import (
    cache_path,
    is_cached,
    read_json,
    read_text,
    write_json,
    write_text,
)


def test_cache_path_structure(tmp_path: Path) -> None:
    path = cache_path(tmp_path, "tns", "ZTF21abc", "json")
    assert path == tmp_path / "tns" / "ZTF21abc.json"


def test_write_and_read_json(tmp_path: Path) -> None:
    data = {"type": "SN Ia", "redshift": 0.05}
    write_json(tmp_path, "tns", "ZTF21abc", data)

    result = read_json(tmp_path, "tns", "ZTF21abc")
    assert result == data


def test_write_and_read_text(tmp_path: Path) -> None:
    content = "col1,col2\na,b\n"
    write_text(tmp_path, "lightcurves", "ZTF21abc", content)

    result = read_text(tmp_path, "lightcurves", "ZTF21abc")
    assert result == content


def test_is_cached_returns_false_when_missing(tmp_path: Path) -> None:
    assert is_cached(tmp_path, "tns", "nonexistent") is False


def test_is_cached_returns_true_when_exists(tmp_path: Path) -> None:
    write_json(tmp_path, "tns", "ZTF21abc", {"test": True})
    assert is_cached(tmp_path, "tns", "ZTF21abc") is True


def test_sanitize_key_rejects_path_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid cache key"):
        cache_path(tmp_path, "tns", "../../etc/passwd", "json")


def test_sanitize_key_rejects_leading_space(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Invalid cache key"):
        cache_path(tmp_path, "tns", " ZTF21abc", "json")
