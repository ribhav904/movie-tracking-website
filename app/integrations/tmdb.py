from datetime import date
from typing import Any

import httpx

from app.db.models.enums import MediaProvider, MediaType
from app.integrations.base import MediaProviderClient
from app.schemas.media import MediaDetail, MediaSummary, PublicRating

API = "https://api.themoviedb.org/3"
IMAGE = "https://image.tmdb.org/t/p/w500"
BACKDROP = "https://image.tmdb.org/t/p/original"


def _date(value: str | None) -> date | None:
    try:
        return date.fromisoformat(value) if value else None
    except ValueError:
        return None


class TMDBClient(MediaProviderClient):
    def __init__(self, client: httpx.AsyncClient, access_token: str) -> None:
        super().__init__(client, rate_per_second=20)
        self.headers = {"Authorization": f"Bearer {access_token}", "accept": "application/json"}

    @staticmethod
    def _validate_type(media_type: MediaType) -> str:
        if media_type not in {MediaType.MOVIE, MediaType.TV}:
            raise ValueError("TMDB supports only movie and tv media types")
        return media_type.value

    def _summary(self, data: dict[str, Any], media_type: MediaType) -> MediaSummary:
        raw_rating = float(data.get("vote_average") or 0)
        rating = None
        if raw_rating > 0:
            rating = PublicRating(
                source="tmdb",
                value=raw_rating,
                count=data.get("vote_count"),
                normalized_10=raw_rating,
            )
        return MediaSummary(
            provider=MediaProvider.TMDB,
            external_id=str(data["id"]),
            media_type=media_type,
            title=data.get("title") or data.get("name") or "Untitled",
            description=data.get("overview") or None,
            release_date=_date(data.get("release_date") or data.get("first_air_date")),
            poster_url=f"{IMAGE}{data['poster_path']}" if data.get("poster_path") else None,
            genres=[str(g["name"]) for g in data.get("genres", [])],
            public_rating=rating,
        )

    async def search(
        self, query: str, media_type: MediaType, *, page: int = 1
    ) -> list[MediaSummary]:
        kind = self._validate_type(media_type)
        response = await self.request(
            "GET",
            f"{API}/search/{kind}",
            headers=self.headers,
            params={"query": query, "page": page, "include_adult": "false"},
        )
        return [self._summary(item, media_type) for item in response.json().get("results", [])[:20]]

    async def detail(self, external_id: str, media_type: MediaType) -> MediaDetail:
        kind = self._validate_type(media_type)
        response = await self.request(
            "GET",
            f"{API}/{kind}/{external_id}",
            headers=self.headers,
            params={"append_to_response": "credits"},
        )
        data = response.json()
        summary = self._summary(data, media_type)
        credits = [
            {
                "name": person.get("name", "Unknown"),
                "role": person.get("job") or "cast",
                "character": person.get("character"),
                "order": person.get("order", 0),
            }
            for person in [
                *data.get("credits", {}).get("cast", [])[:15],
                *data.get("credits", {}).get("crew", [])[:15],
            ]
        ]
        extra: dict[str, object] = {"runtime_minutes": data.get("runtime")}
        if media_type == MediaType.TV:
            # One title request is enough for season-level tracking. Fetching
            # every season and episode here made a single show page issue an
            # unbounded burst of provider calls.
            seasons = [
                {
                    "season_number": season.get("season_number"),
                    "title": season.get("name"),
                    "air_date": season.get("air_date"),
                    "episode_count": season.get("episode_count"),
                    "episodes": [],
                }
                for season in data.get("seasons", [])
                if season.get("season_number") is not None
            ]
            extra.update(
                {
                    "status": data.get("status"),
                    "season_count": data.get("number_of_seasons"),
                    "episode_count": data.get("number_of_episodes"),
                    "seasons": seasons,
                }
            )
        return MediaDetail(
            **summary.model_dump(),
            original_title=data.get("original_title") or data.get("original_name"),
            original_language=data.get("original_language"),
            backdrop_url=f"{BACKDROP}{data['backdrop_path']}"
            if data.get("backdrop_path")
            else None,
            credits=credits,
            extra=extra,
        )

    async def discover(self, media_type: MediaType, *, page: int = 1) -> list[MediaSummary]:
        kind = self._validate_type(media_type)
        response = await self.request(
            "GET", f"{API}/trending/{kind}/week", headers=self.headers, params={"page": page}
        )
        return [self._summary(item, media_type) for item in response.json().get("results", [])[:20]]
