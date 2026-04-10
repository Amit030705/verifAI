from __future__ import annotations

import asyncio
from typing import Any

import httpx

from app.utils.errors import PlatformServiceError


async def request_with_retry(
    client: httpx.AsyncClient,
    *,
    method: str,
    url: str,
    platform: str,
    retries: int = 2,
    backoff_seconds: float = 0.5,
    **kwargs: Any,
) -> httpx.Response:
    last_error: Exception | None = None

    for attempt in range(retries + 1):
        try:
            response = await client.request(method=method, url=url, **kwargs)

            if response.status_code >= 500:
                raise httpx.HTTPStatusError(
                    f"Server error from {platform}: {response.status_code}",
                    request=response.request,
                    response=response,
                )

            return response

        except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
            last_error = exc
            if attempt == retries:
                break
            await asyncio.sleep(backoff_seconds * (2**attempt))

    raise PlatformServiceError(
        platform=platform,
        message=f"{platform} service temporarily unavailable.",
        status_code=503,
    ) from last_error
