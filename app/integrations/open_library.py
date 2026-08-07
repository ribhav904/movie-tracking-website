from typing import Any

import httpx

from app.db.models.enums import MediaProvider, MediaType
from app.integrations.base import MediaProviderClient
from app.schemas.media import MediaDetail, MediaSummary


class OpenLibraryClient(MediaProviderClient):
    def __init__(self, client: httpx.AsyncClient, contact: str) -> None:
        super().__init__(client, rate_per_second=3)
        self.headers = {"User-Agent": f"EntertainmentTracker ({contact})"}

    @staticmethod
    def _summary(data: dict[str, Any]) -> MediaSummary:
        cover_id = data.get("cover_i")
        return MediaSummary(
            provider=MediaProvider.OPEN_LIBRARY,
            external_id=str(data.get("key", "")).removeprefix("/works/"),
            media_type=MediaType.BOOK,
            title=data.get("title") or "Untitled",
            release_date=None,
            poster_url=f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            if cover_id
            else None,
            genres=data.get("subject", [])[:10],
        )

    async def search(
        self, query: str, media_type: MediaType, *, page: int = 1
    ) -> list[MediaSummary]:
        if media_type != MediaType.BOOK:
            raise ValueError("Open Library supports only books")
        response = await self.request(
            "GET",
            "https://openlibrary.org/search.json",
            headers=self.headers,
            params={"q": query, "page": page, "limit": 20},
        )
        return [self._summary(item) for item in response.json().get("docs", [])]

    async def detail(self, external_id: str, media_type: MediaType) -> MediaDetail:
        if media_type != MediaType.BOOK:
            raise ValueError("Open Library supports only books")
        response = await self.request(
            "GET", f"https://openlibrary.org/works/{external_id}.json", headers=self.headers
        )
        data = response.json()
        cover_id = (data.get("covers") or [None])[0]
        description = data.get("description")
        if isinstance(description, dict):
            description = description.get("value")
        return MediaDetail(
            provider=MediaProvider.OPEN_LIBRARY,
            external_id=external_id,
            media_type=MediaType.BOOK,
            title=data.get("title") or "Untitled",
            description=description,
            poster_url=f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg"
            if cover_id
            else None,
            genres=data.get("subjects", [])[:20],
            extra={},
        )
