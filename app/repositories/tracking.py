from datetime import date
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import MediaItem, TVSeason
from app.db.models.tracking import ConsumptionRecord, LibraryEntry
from app.schemas.tracking import ConsumptionCreate, ConsumptionUpdate


class TrackingRepository:
    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def get(self, record_id: UUID) -> ConsumptionRecord | None:
        return cast(
            ConsumptionRecord | None,
            await self.session.scalar(
                select(ConsumptionRecord).where(
                    ConsumptionRecord.id == record_id,
                    ConsumptionRecord.user_id == self.user_id,
                )
            ),
        )

    async def list_for_entry(self, entry_id: UUID) -> list[ConsumptionRecord]:
        rows = await self.session.scalars(
            select(ConsumptionRecord)
            .where(
                ConsumptionRecord.library_entry_id == entry_id,
                ConsumptionRecord.user_id == self.user_id,
            )
            .order_by(
                ConsumptionRecord.completed_on.desc().nullslast(),
                ConsumptionRecord.sequence_number.desc(),
            )
        )
        return list(rows)

    async def create(self, entry: LibraryEntry, payload: ConsumptionCreate) -> ConsumptionRecord:
        sequence = await self.session.scalar(
            select(func.coalesce(func.max(ConsumptionRecord.sequence_number), 0) + 1).where(
                ConsumptionRecord.library_entry_id == entry.id
            )
        )
        record = ConsumptionRecord(
            user_id=self.user_id,
            library_entry_id=entry.id,
            sequence_number=int(sequence or 1),
            **payload.model_dump(),
        )
        self.session.add(record)
        await self.session.flush()
        return record

    async def update(
        self, record: ConsumptionRecord, payload: ConsumptionUpdate
    ) -> ConsumptionRecord:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, key, value)
        await self.session.flush()
        return record

    async def delete(self, record: ConsumptionRecord) -> None:
        await self.session.delete(record)
        await self.session.flush()

    async def count_for_entry(self, entry_id: UUID) -> int:
        value = await self.session.scalar(
            select(func.count(ConsumptionRecord.id)).where(
                ConsumptionRecord.library_entry_id == entry_id,
                ConsumptionRecord.user_id == self.user_id,
            )
        )
        return int(value or 0)

    async def season_belongs_to_media(self, season_id: UUID, media_id: UUID) -> bool:
        value = await self.session.scalar(
            select(TVSeason.id).where(TVSeason.id == season_id, TVSeason.media_id == media_id)
        )
        return value is not None

    async def history(
        self, *, offset: int = 0, limit: int = 100
    ) -> list[tuple[ConsumptionRecord, MediaItem, TVSeason | None]]:
        rows = await self.session.execute(
            select(ConsumptionRecord, MediaItem, TVSeason)
            .join(LibraryEntry, LibraryEntry.id == ConsumptionRecord.library_entry_id)
            .join(MediaItem, MediaItem.id == LibraryEntry.media_id)
            .outerjoin(TVSeason, TVSeason.id == ConsumptionRecord.season_id)
            .where(
                ConsumptionRecord.user_id == self.user_id,
                ConsumptionRecord.completed_on.is_not(None),
            )
            .order_by(ConsumptionRecord.completed_on.desc(), ConsumptionRecord.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return [(row[0], row[1], row[2]) for row in rows]

    async def year_counts(self, year: int) -> list[tuple[date, int]]:
        rows = await self.session.execute(
            select(ConsumptionRecord.completed_on, func.count(ConsumptionRecord.id))
            .where(
                ConsumptionRecord.user_id == self.user_id,
                ConsumptionRecord.completed_on.is_not(None),
                func.extract("year", ConsumptionRecord.completed_on) == year,
            )
            .group_by(ConsumptionRecord.completed_on)
            .order_by(ConsumptionRecord.completed_on)
        )
        return [(row[0], int(row[1])) for row in rows if row[0] is not None]

    async def completed_in_year(self, year: int) -> int:
        value = await self.session.scalar(
            select(func.count(ConsumptionRecord.id)).where(
                ConsumptionRecord.user_id == self.user_id,
                ConsumptionRecord.completed_on.is_not(None),
                func.extract("year", ConsumptionRecord.completed_on) == year,
            )
        )
        return int(value or 0)
