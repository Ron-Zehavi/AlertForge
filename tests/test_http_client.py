"""Tests for HTTP client with retry."""

from __future__ import annotations

import httpx
import pytest

from alertforge.utils.http_client import fetch_json, fetch_text


def _mock_transport(
    responses: list[httpx.Response],
) -> httpx.MockTransport:
    """Create a mock transport that returns responses in order."""
    call_count = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        idx = min(call_count, len(responses) - 1)
        call_count += 1
        return responses[idx]

    return httpx.MockTransport(handler)


@pytest.fixture
def ok_json_client() -> httpx.AsyncClient:
    transport = _mock_transport([httpx.Response(200, json={"status": "ok"})])
    return httpx.AsyncClient(transport=transport)


@pytest.fixture
def ok_text_client() -> httpx.AsyncClient:
    transport = _mock_transport([httpx.Response(200, text="col1,col2\na,b\n")])
    return httpx.AsyncClient(transport=transport)


async def test_fetch_json_success(ok_json_client: httpx.AsyncClient) -> None:
    result = await fetch_json("https://example.com/api", client=ok_json_client)
    assert result == {"status": "ok"}


async def test_fetch_text_success(ok_text_client: httpx.AsyncClient) -> None:
    result = await fetch_text("https://example.com/data.csv", client=ok_text_client)
    assert "col1" in result


async def test_fetch_json_post() -> None:
    received: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        received["method"] = request.method
        return httpx.Response(200, json={"posted": True})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    result = await fetch_json(
        "https://example.com/api",
        method="POST",
        data={"key": "value"},
        client=client,
    )
    assert result == {"posted": True}
    assert received["method"] == "POST"


async def test_fetch_json_retry_on_500() -> None:
    transport = _mock_transport(
        [
            httpx.Response(500, json={"error": "internal"}),
            httpx.Response(200, json={"status": "ok"}),
        ]
    )
    client = httpx.AsyncClient(transport=transport)
    result = await fetch_json("https://example.com/api", client=client, retries=2)
    assert result == {"status": "ok"}


async def test_fetch_json_retry_on_429() -> None:
    transport = _mock_transport(
        [
            httpx.Response(429, json={"error": "rate limited"}),
            httpx.Response(200, json={"status": "ok"}),
        ]
    )
    client = httpx.AsyncClient(transport=transport)
    result = await fetch_json("https://example.com/api", client=client, retries=2)
    assert result == {"status": "ok"}


async def test_fetch_json_no_retry_on_404() -> None:
    transport = _mock_transport([httpx.Response(404, text="not found")])
    client = httpx.AsyncClient(transport=transport)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        await fetch_json("https://example.com/api", client=client)
    assert exc_info.value.response.status_code == 404


async def test_fetch_json_exhausts_retries() -> None:
    transport = _mock_transport([httpx.Response(500, json={"error": "fail"})] * 3)
    client = httpx.AsyncClient(transport=transport)
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_json("https://example.com/api", client=client, retries=3)
