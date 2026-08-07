from datetime import date
from typing import Any

import httpx

from app.db.models.enums import MediaProvider, MediaType
from app.integrations.base import MediaProviderClient
from app.schemas.media import MediaDetail, MediaSummary, PublicRating


def _published_date(value: str | None) -> date | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
        try:
            from datetime import datetime

            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


class GoogleBooksClient(MediaProviderClient):
    def __init__(self, client: httpx.AsyncClient, api_key: str) -> None:
        super().__init__(client, rate_per_second=10)
        self.api_key = api_key

    @staticmethod
    def _summary(data: dict[str, Any]) -> MediaSummary:
        info = data.get("volumeInfo", {})
        raw_rating = info.get("averageRating")
        rating = None
        if raw_rating:
            rating = PublicRating(
                source="google_books",
                value=float(raw_rating),
                scale=5,
                count=info.get("ratingsCount"),
                normalized_10=float(raw_rating) * 2,
            )
        image = info.get("imageLinks", {}).get("thumbnail")
        return MediaSummary(
            provider=MediaProvider.GOOGLE_BOOKS,
            external_id=data["id"],
            media_type=MediaType.BOOK,
            title=info.get("title") or "Untitled",
            description=info.get("description"),
            release_date=_published_date(info.get("publishedDate")),
            poster_url=image.replace("http://", "https://") if image else None,
            genres=info.get("categories", []),
            public_rating=rating,
        )

    async def search(
        self, query: str, media_type: MediaType, *, page: int = 1
    ) -> list[MediaSummary]:
        if media_type != MediaType.BOOK:
            raise ValueError("Google Books supports only books")
        response = await self.request(
            "GET",
            "https://www.googleapis.com/books/v1/volumes",
            params={
                "q": query,
                "key": self.api_key,
                "startIndex": (page - 1) * 20,
                "maxResults": 20,
            },
        )
        return [self._summary(item) for item in response.json().get("items", [])]

    async def detail(self, external_id: str, media_type: MediaType) -> MediaDetail:
        if media_type != MediaType.BOOK:
            raise ValueError("Google Books supports only books")
        response = await self.request(
            "GET",
            f"https://www.googleapis.com/books/v1/volumes/{external_id}",
            params={"key": self.api_key},
        )
        data = response.json()
        info = data.get("volumeInfo", {})
        identifiers = {
            item["type"]: item["identifier"] for item in info.get("industryIdentifiers", [])
        }
        summary = self._summary(data)
        return MediaDetail(
            **summary.model_dump(),
            original_language=info.get("language"),
            credits=[
                {"name": name, "role": "author", "character": None, "order": order}
                for order, name in enumerate(info.get("authors", []))
            ],
            extra={
                "authors": info.get("authors", []),
                "publisher": info.get("publisher"),
                "page_count": info.get("pageCount"),
                "isbn_10": identifiers.get("ISBN_10"),
                "isbn_13": identifiers.get("ISBN_13"),
            },
        )

    async def discover(self, media_type: MediaType, *, page: int = 1) -> list[MediaSummary]:
        return await self.search("subject:fiction", media_type, page=page)
