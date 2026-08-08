import time
from datetime import UTC, datetime
from typing import Any, cast

import httpx

from app.db.models.enums import DiscoverMode, MediaProvider, MediaType
from app.integrations.base import MediaProviderClient
from app.schemas.media import MediaDetail, MediaSummary, PublicRating


class IGDBClient(MediaProviderClient):
    def __init__(self, client: httpx.AsyncClient, client_id: str, client_secret: str) -> None:
        super().__init__(client, rate_per_second=4)
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = ""
        self._token_expires_at = 0.0

    async def _headers(self) -> dict[str, str]:
        if not self._token or time.monotonic() >= self._token_expires_at:
            response = await self.client.post(
                "https://id.twitch.tv/oauth2/token",
                params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
            )
            response.raise_for_status()
            payload = response.json()
            self._token = payload["access_token"]
            self._token_expires_at = time.monotonic() + int(payload["expires_in"]) - 60
        return {"Client-ID": self.client_id, "Authorization": f"Bearer {self._token}"}

    @staticmethod
    def _summary(data: dict[str, Any]) -> MediaSummary:
        raw_rating = data.get("total_rating") or data.get("rating")
        rating = None
        if raw_rating:
            rating = PublicRating(
                source="igdb",
                value=float(raw_rating),
                scale=100,
                count=data.get("total_rating_count") or data.get("rating_count"),
                normalized_10=float(raw_rating) / 10,
            )
        timestamp = data.get("first_release_date")
        release_date = datetime.fromtimestamp(timestamp, tz=UTC).date() if timestamp else None
        cover = data.get("cover", {}).get("image_id")
        return MediaSummary(
            provider=MediaProvider.IGDB,
            external_id=str(data["id"]),
            media_type=MediaType.GAME,
            title=data.get("name") or "Untitled",
            description=data.get("summary"),
            release_date=release_date,
            poster_url=f"https://images.igdb.com/igdb/image/upload/t_cover_big/{cover}.jpg"
            if cover
            else None,
            genres=[g["name"] for g in data.get("genres", [])],
            public_rating=rating,
        )

    async def _query(self, body: str) -> list[dict[str, Any]]:
        response = await self.request(
            "POST", "https://api.igdb.com/v4/games", headers=await self._headers(), content=body
        )
        return cast(list[dict[str, Any]], response.json())

    async def search(
        self, query: str, media_type: MediaType, *, page: int = 1
    ) -> list[MediaSummary]:
        if media_type != MediaType.GAME:
            raise ValueError("IGDB supports only games")
        safe_query = query.replace('"', "")
        offset = max(page - 1, 0) * 20
        fields = (
            "id,name,summary,first_release_date,total_rating,total_rating_count,"
            "cover.image_id,genres.name"
        )
        rows = await self._query(
            f'search "{safe_query}"; fields {fields}; limit 20; offset {offset};'
        )
        return [self._summary(item) for item in rows]

    async def detail(self, external_id: str, media_type: MediaType) -> MediaDetail:
        if media_type != MediaType.GAME:
            raise ValueError("IGDB supports only games")
        fields = (
            "id,name,summary,first_release_date,total_rating,total_rating_count,cover.image_id,"
            "genres.name,platforms.name,involved_companies.company.name,game_modes.name"
        )
        rows = await self._query(f"fields {fields}; where id = {int(external_id)}; limit 1;")
        if not rows:
            request = httpx.Request("POST", "https://api.igdb.com/v4/games")
            response = httpx.Response(404, request=request)
            raise httpx.HTTPStatusError("IGDB item not found", request=request, response=response)
        data = rows[0]
        summary = self._summary(data)
        return MediaDetail(
            **summary.model_dump(),
            extra={
                "platforms": [p["name"] for p in data.get("platforms", [])],
                "companies": [
                    c["company"]["name"]
                    for c in data.get("involved_companies", [])
                    if c.get("company")
                ],
                "game_modes": [m["name"] for m in data.get("game_modes", [])],
            },
        )

    async def discover(
        self, media_type: MediaType, *, page: int = 1, mode: DiscoverMode = DiscoverMode.TRENDING
    ) -> list[MediaSummary]:
        if media_type != MediaType.GAME:
            raise ValueError("IGDB supports only games")
        offset = max(page - 1, 0) * 20
        fields = (
            "id,name,summary,first_release_date,total_rating,total_rating_count,"
            "cover.image_id,genres.name"
        )
        if mode == DiscoverMode.TOP_RATED:
            where, order = "total_rating != null", "total_rating desc"
        elif mode == DiscoverMode.RECENT:
            where = f"first_release_date != null & first_release_date <= {int(time.time())}"
            order = "first_release_date desc"
        else:
            # IGDB does not expose a dedicated trending list through this endpoint;
            # rating volume is the reliable, supported popularity proxy.
            where, order = "total_rating_count != null", "total_rating_count desc"
        rows = await self._query(
            f"fields {fields}; where {where}; sort {order}; limit 20; offset {offset};"
        )
        return [self._summary(item) for item in rows]
