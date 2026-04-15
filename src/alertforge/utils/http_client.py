"""Thin async HTTP client with retry and timeout."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_DEFAULT_RETRIES = 3
_DEFAULT_BACKOFF_BASE = 2.0
_DEFAULT_TIMEOUT = 30.0


async def fetch_json(
    url: str,
    *,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    retries: int = _DEFAULT_RETRIES,
    client: httpx.AsyncClient | None = None,
) -> Any:
    """Fetch JSON from a URL with retry and exponential backoff.

    Args:
        url: The URL to fetch.
        method: HTTP method (GET or POST).
        data: Form data or JSON body for POST requests.
        headers: Additional headers.
        timeout: Request timeout in seconds.
        retries: Number of retry attempts.
        client: Optional pre-configured httpx client (for testing).

    Returns:
        Parsed JSON response.

    Raises:
        httpx.HTTPStatusError: If the request fails after all retries.
    """
    should_close = client is None
    client = client or httpx.AsyncClient(timeout=timeout)

    try:
        return await _fetch_with_retry(
            client, url, method=method, data=data, headers=headers, retries=retries
        )
    finally:
        if should_close:
            await client.aclose()


async def fetch_text(
    url: str,
    *,
    method: str = "GET",
    data: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: float = _DEFAULT_TIMEOUT,
    retries: int = _DEFAULT_RETRIES,
    client: httpx.AsyncClient | None = None,
) -> str:
    """Fetch text content from a URL with retry and exponential backoff."""
    should_close = client is None
    client = client or httpx.AsyncClient(timeout=timeout)

    try:
        result: str = await _fetch_with_retry(
            client,
            url,
            method=method,
            data=data,
            headers=headers,
            retries=retries,
            as_json=False,
        )
        return result
    finally:
        if should_close:
            await client.aclose()


async def _fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    method: str,
    data: dict[str, Any] | None,
    headers: dict[str, str] | None,
    retries: int,
    as_json: bool = True,
) -> Any:
    last_exc: Exception | None = None

    for attempt in range(retries):
        try:
            if method.upper() == "POST":
                resp = await client.post(url, data=data, headers=headers)
            else:
                resp = await client.get(url, headers=headers, params=data)

            resp.raise_for_status()
            return resp.json() if as_json else resp.text

        except (httpx.HTTPStatusError, httpx.TransportError) as exc:
            last_exc = exc
            if isinstance(exc, httpx.HTTPStatusError) and exc.response.status_code < 500:
                if exc.response.status_code != 429:
                    raise

            wait = _DEFAULT_BACKOFF_BASE**attempt
            logger.warning(
                "Request to %s failed (attempt %d/%d): %s. Retrying in %.1fs",
                url,
                attempt + 1,
                retries,
                exc,
                wait,
            )
            await asyncio.sleep(wait)

    assert last_exc is not None  # noqa: S101
    raise last_exc
