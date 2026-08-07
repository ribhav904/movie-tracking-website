import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any

import httpx

from app.db.models.enums import MediaType
from app.schemas.media import MediaDetail, MediaSummary


class AsyncRateLimiter:
    def __init__(self, rate_per_second: float) -> None:
        self._interval = 1 / rate_per_second
        self._last_request = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        async with self._lock:
            delay = self._interval - (time.monotonic() - self._last_request)
            if delay > 0:
                await asyncio.sleep(delay)
            self._last_request = time.monotonic()


class MediaProviderClient(ABC):
    def __init__(self, client: httpx.AsyncClient, rate_per_second: float) -> None:
        self.client = client
        self.limiter = AsyncRateLimiter(rate_per_second)

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        await self.limiter.wait()
        response = await self.client.request(method, url, **kwargs)
        if response.status_code == 429:
            retry_after = min(float(response.headers.get("Retry-After", "1")), 3.0)
            await asyncio.sleep(retry_after)
            await self.limiter.wait()
            response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    @abstractmethod
    async def search(
        self, query: str, media_type: MediaType, *, page: int = 1
    ) -> list[MediaSummary]: ...

    @abstractmethod
    async def detail(self, external_id: str, media_type: MediaType) -> MediaDetail: ...

    async def discover(self, media_type: MediaType, *, page: int = 1) -> list[MediaSummary]:
        return []
