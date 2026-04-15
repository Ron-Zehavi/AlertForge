"""Tests for rate limiter."""

from __future__ import annotations

import time

from alertforge.utils.rate_limiter import RateLimiter


async def test_rate_limiter_enforces_interval() -> None:
    limiter = RateLimiter(requests_per_second=100.0)  # fast for testing

    start = time.monotonic()
    async with limiter:
        pass
    async with limiter:
        pass
    elapsed = time.monotonic() - start

    # Two requests at 100 rps should take at least 0.01s
    assert elapsed >= 0.009


async def test_rate_limiter_first_request_immediate() -> None:
    limiter = RateLimiter(requests_per_second=1.0)

    start = time.monotonic()
    async with limiter:
        pass
    elapsed = time.monotonic() - start

    # First request should be nearly immediate
    assert elapsed < 0.1
