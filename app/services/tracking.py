from datetime import date
from uuid import UUID

from app.core.exceptions import AppError, NotFoundError
from app.db.models.catalog import TVSeason
from app.db.models.enums import LibraryStatus, MediaType
from app.db.models.tracking import ConsumptionRecord, LibraryEntry
from app.repositories.catalog import CatalogRepository
from app.repositories.library import LibraryRepository
from app.repositories.tracking import TrackingRepository
from app.schemas.tracking import (
    ConsumptionCreate,
    ConsumptionUpdate,
    HistoryItem,
    SeasonSummary,
)


class TrackingService:
    def __init__(
        self,
        repository: TrackingRepository,
        library_repository: LibraryRepository,
        catalog_repository: CatalogRepository,
    ) -> None:
        self.repository = repository
        self.library_repository = library_repository
        self.catalog_repository = catalog_repository

    async def record(self, entry_id: UUID, payload: ConsumptionCreate) -> ConsumptionRecord:
        entry = await self._entry(entry_id)
        media = await self.catalog_repository.get(entry.media_id)
        if media is None:
            raise NotFoundError("MEDIA_NOT_FOUND", "The media item does not exist.")
        if media.media_type == MediaType.TV:
            if payload.season_id is None:
                raise AppError(
                    "TV_SEASON_REQUIRED", "Choose a season when recording a television show."
                )
            if not await self.repository.season_belongs_to_media(payload.season_id, entry.media_id):
                raise NotFoundError(
                    "TV_SEASON_NOT_FOUND", "The season does not belong to this show."
                )
        elif payload.season_id is not None:
            raise AppError(
                "SEASON_NOT_ALLOWED", "Only television completion records can reference a season."
            )

        record = await self.repository.create(entry, payload)
        await self._refresh_entry(entry)
        return record

    async def update(self, record_id: UUID, payload: ConsumptionUpdate) -> ConsumptionRecord:
        record = await self._record(record_id)
        record = await self.repository.update(record, payload)
        await self._refresh_entry(await self._entry(record.library_entry_id))
        return record

    async def delete(self, record_id: UUID) -> None:
        record = await self._record(record_id)
        entry = await self._entry(record.library_entry_id)
        await self.repository.delete(record)
        await self._refresh_entry(entry)

    async def list_records(self, entry_id: UUID) -> list[ConsumptionRecord]:
        await self._entry(entry_id)
        return await self.repository.list_for_entry(entry_id)

    async def history(self, *, offset: int, limit: int) -> list[HistoryItem]:
        rows = await self.repository.history(offset=offset, limit=limit)
        return [
            HistoryItem(
                id=record.id,
                library_entry_id=record.library_entry_id,
                media_id=media.id,
                season_id=record.season_id,
                sequence_number=record.sequence_number,
                completed_on=record.completed_on,
                rating=float(record.rating) if record.rating is not None else None,
                notes=record.notes,
                created_at=record.created_at,
                updated_at=record.updated_at,
                title=media.title,
                media_type=media.media_type.value,
                poster_url=media.poster_url,
                season_title=season.title if season else None,
                season_number=season.season_number if season else None,
            )
            for record, media, season in rows
        ]

    async def season_summaries(self, media_id: UUID) -> list[SeasonSummary]:
        entry = await self.library_repository.get_by_media(media_id)
        records = await self.repository.list_for_entry(entry.id) if entry else []
        seasons = await self.catalog_repository.list_seasons(media_id)
        return [self._season_summary(season, records) for season in seasons]

    async def _refresh_entry(self, entry: LibraryEntry) -> None:
        media = await self.catalog_repository.get(entry.media_id)
        if media is None:
            return
        records = await self.repository.list_for_entry(entry.id)
        if media.media_type != MediaType.TV:
            entry.status = LibraryStatus.COMPLETED if records else LibraryStatus.PLANNED
            latest_rating = next(
                (record.rating for record in records if record.rating is not None), None
            )
            entry.manual_rating = latest_rating
            return

        watched_seasons = {record.season_id for record in records if record.season_id is not None}
        seasons = [
            season
            for season in await self.catalog_repository.list_seasons(entry.media_id)
            if season.season_number > 0
            and (season.air_date is None or season.air_date <= date.today())
        ]
        if not watched_seasons:
            entry.status = LibraryStatus.PLANNED
            return
        if seasons and all(season.id in watched_seasons for season in seasons):
            details = await self.catalog_repository.tv_details(entry.media_id)
            entry.status = (
                LibraryStatus.COMPLETED
                if details and details.status and details.status.casefold() == "ended"
                else LibraryStatus.CAUGHT_UP
            )
        else:
            entry.status = LibraryStatus.IN_PROGRESS

    @staticmethod
    def _season_summary(season: TVSeason, records: list[ConsumptionRecord]) -> SeasonSummary:
        season_records = [record for record in records if record.season_id == season.id]
        latest = season_records[0] if season_records else None
        return SeasonSummary(
            id=season.id,
            season_number=season.season_number,
            title=season.title,
            air_date=season.air_date,
            episode_count=season.episode_count,
            watched_count=len(season_records),
            latest_completed_on=latest.completed_on if latest else None,
            latest_rating=float(latest.rating) if latest and latest.rating is not None else None,
        )

    async def _entry(self, entry_id: UUID) -> LibraryEntry:
        entry = await self.library_repository.get(entry_id)
        if entry is None:
            raise NotFoundError("LIBRARY_ENTRY_NOT_FOUND", "The library entry does not exist.")
        return entry

    async def _record(self, record_id: UUID) -> ConsumptionRecord:
        record = await self.repository.get(record_id)
        if record is None:
            raise NotFoundError(
                "CONSUMPTION_RECORD_NOT_FOUND", "The completion record does not exist."
            )
        return record
