from datetime import UTC, date, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import (
    BookDetails,
    GameDetails,
    MediaCredit,
    MediaGenre,
    MediaItem,
    MediaSource,
    MovieDetails,
    TVDetails,
    TVEpisode,
    TVSeason,
)
from app.db.models.enums import MediaProvider, MediaType
from app.schemas.media import MediaDetail


class CatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, media_id: UUID) -> MediaItem | None:
        return await self.session.get(MediaItem, media_id)

    async def get_by_source(
        self, provider: MediaProvider, media_type: MediaType, external_id: str
    ) -> tuple[MediaItem, MediaSource] | None:
        result = await self.session.execute(
            select(MediaItem, MediaSource)
            .join(MediaSource, MediaSource.media_id == MediaItem.id)
            .where(
                MediaSource.provider == provider,
                MediaSource.media_type == media_type,
                MediaSource.external_id == external_id,
            )
        )
        row = result.one_or_none()
        return cast(tuple[MediaItem, MediaSource], tuple(row)) if row else None

    async def upsert(self, detail: MediaDetail) -> MediaItem:
        existing = await self.get_by_source(detail.provider, detail.media_type, detail.external_id)
        rating = detail.public_rating
        now = datetime.now(UTC)
        if existing:
            item, source = existing
            item.title = detail.title
            item.original_title = detail.original_title
            item.description = detail.description
            item.release_date = detail.release_date
            item.original_language = detail.original_language
            item.poster_url = detail.poster_url
            item.backdrop_url = detail.backdrop_url
            item.public_rating = rating.normalized_10 if rating else None
            item.public_rating_count = rating.count if rating else None
            item.public_rating_source = rating.source if rating else None
            item.cached_at = now
            source.raw_rating = rating.value if rating else None
            source.raw_rating_scale = rating.scale if rating else None
            source.raw_rating_count = rating.count if rating else None
            source.normalized_payload = detail.model_dump(mode="json")
            source.fetched_at = now
        else:
            item = MediaItem(
                media_type=detail.media_type,
                title=detail.title,
                original_title=detail.original_title,
                description=detail.description,
                release_date=detail.release_date,
                original_language=detail.original_language,
                poster_url=detail.poster_url,
                backdrop_url=detail.backdrop_url,
                public_rating=rating.normalized_10 if rating else None,
                public_rating_count=rating.count if rating else None,
                public_rating_source=rating.source if rating else None,
                cached_at=now,
            )
            self.session.add(item)
            await self.session.flush()
            source = MediaSource(
                media_id=item.id,
                provider=detail.provider,
                media_type=detail.media_type,
                external_id=detail.external_id,
                raw_rating=rating.value if rating else None,
                raw_rating_scale=rating.scale if rating else None,
                raw_rating_count=rating.count if rating else None,
                normalized_payload=detail.model_dump(mode="json"),
                fetched_at=now,
            )
            self.session.add(source)

        await self.session.execute(delete(MediaGenre).where(MediaGenre.media_id == item.id))
        await self.session.execute(delete(MediaCredit).where(MediaCredit.media_id == item.id))
        self.session.add_all([MediaGenre(media_id=item.id, name=name) for name in detail.genres])
        self.session.add_all(
            [
                MediaCredit(
                    media_id=item.id,
                    name=str(credit["name"]),
                    role=str(credit["role"]),
                    character=str(credit["character"]) if credit.get("character") else None,
                    sort_order=int(credit.get("order") or 0),
                )
                for credit in detail.credits
            ]
        )
        await self._upsert_type_details(item.id, detail)
        await self.session.flush()
        return item

    async def _upsert_type_details(self, media_id: UUID, detail: MediaDetail) -> None:
        if detail.media_type == MediaType.MOVIE:
            movie = await self.session.get(MovieDetails, media_id) or MovieDetails(
                media_id=media_id
            )
            movie.runtime_minutes = _as_int(detail.extra.get("runtime_minutes"))
            self.session.add(movie)
        elif detail.media_type == MediaType.TV:
            tv = await self.session.get(TVDetails, media_id) or TVDetails(media_id=media_id)
            tv.status = _as_str(detail.extra.get("status"))
            tv.season_count = _as_int(detail.extra.get("season_count"))
            tv.episode_count = _as_int(detail.extra.get("episode_count"))
            self.session.add(tv)
            await self._upsert_tv_structure(media_id, detail.extra.get("seasons"))
        elif detail.media_type == MediaType.GAME:
            game = await self.session.get(GameDetails, media_id) or GameDetails(media_id=media_id)
            game.platforms = _as_str_list(detail.extra.get("platforms"))
            game.companies = _as_str_list(detail.extra.get("companies"))
            game.game_modes = _as_str_list(detail.extra.get("game_modes"))
            self.session.add(game)
        else:
            book = await self.session.get(BookDetails, media_id) or BookDetails(media_id=media_id)
            book.isbn_10 = _as_str(detail.extra.get("isbn_10"))
            book.isbn_13 = _as_str(detail.extra.get("isbn_13"))
            book.authors = _as_str_list(detail.extra.get("authors"))
            book.publisher = _as_str(detail.extra.get("publisher"))
            book.page_count = _as_int(detail.extra.get("page_count"))
            self.session.add(book)

    async def _upsert_tv_structure(self, media_id: UUID, value: object) -> None:
        if not isinstance(value, list):
            return
        existing_seasons = {
            season.season_number: season
            for season in await self.session.scalars(
                select(TVSeason).where(TVSeason.media_id == media_id)
            )
        }
        for raw_season in value:
            if not isinstance(raw_season, dict):
                continue
            season_number = _as_int(raw_season.get("season_number"))
            if season_number is None:
                continue
            season = existing_seasons.get(season_number) or TVSeason(
                media_id=media_id, season_number=season_number
            )
            season.title = _as_str(raw_season.get("title"))
            season.air_date = _as_date(raw_season.get("air_date"))
            season.episode_count = _as_int(raw_season.get("episode_count"))
            self.session.add(season)
            await self.session.flush()
            existing_episodes = {
                episode.episode_number: episode
                for episode in await self.session.scalars(
                    select(TVEpisode).where(TVEpisode.season_id == season.id)
                )
            }
            episodes = raw_season.get("episodes")
            if not isinstance(episodes, list):
                continue
            for raw_episode in episodes:
                if not isinstance(raw_episode, dict):
                    continue
                episode_number = _as_int(raw_episode.get("episode_number"))
                if episode_number is None:
                    continue
                episode = existing_episodes.get(episode_number) or TVEpisode(
                    season_id=season.id,
                    episode_number=episode_number,
                    title="Untitled",
                )
                episode.title = _as_str(raw_episode.get("title")) or "Untitled"
                episode.description = _as_str(raw_episode.get("description"))
                episode.air_date = _as_date(raw_episode.get("air_date"))
                episode.runtime_minutes = _as_int(raw_episode.get("runtime_minutes"))
                self.session.add(episode)


def _as_int(value: object) -> int | None:
    return int(value) if isinstance(value, int | float) else None


def _as_str(value: object) -> str | None:
    return str(value) if value is not None else None


def _as_str_list(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def _as_date(value: object) -> date | None:
    try:
        return date.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        return None
