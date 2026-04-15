"""Standalone token-bucket rate limiter for API calls."""

from __future__ import annotations

import asyncio
import time


class RateLimiter:
    """Token-bucket rate limiter.

    Each ingest module creates its own instance with the appropriate
    rate for that API. The limiter is not baked into the HTTP client.

    Usage:
        limiter = RateLimiter(requests_per_second=0.5)
        async with limiter:
            await fetch_json(url)
    """

    def __init__(self, requests_per_second: float) -> None:
        self._min_interval = 1.0 / requests_per_second
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        """Wait until a request is allowed."""
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
            self._last_request = time.monotonic()

    async def __aenter__(self) -> RateLimiter:
        await self.acquire()
        return self

    async def __aexit__(self, *args: object) -> None:
        pass
