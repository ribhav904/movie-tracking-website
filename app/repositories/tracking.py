from datetime import date
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import TVEpisode, TVSeason
from app.db.models.enums import ActivityKind, CycleState
from app.db.models.tracking import ActivityEvent, ConsumptionCycle, LibraryEntry
from app.schemas.tracking import ActivityCreate, CycleCreate, CycleUpdate


class TrackingRepository:
    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def get_cycle(self, cycle_id: UUID) -> ConsumptionCycle | None:
        return cast(
            ConsumptionCycle | None,
            await self.session.scalar(
                select(ConsumptionCycle).where(
                    ConsumptionCycle.id == cycle_id,
                    ConsumptionCycle.user_id == self.user_id,
                )
            ),
        )

    async def get_active_cycle(self, entry_id: UUID) -> ConsumptionCycle | None:
        return cast(
            ConsumptionCycle | None,
            await self.session.scalar(
                select(ConsumptionCycle)
                .where(
                    ConsumptionCycle.library_entry_id == entry_id,
                    ConsumptionCycle.user_id == self.user_id,
                    ConsumptionCycle.state == CycleState.IN_PROGRESS,
                )
                .order_by(ConsumptionCycle.sequence_number.desc())
                .limit(1)
            ),
        )

    async def create_cycle(self, entry: LibraryEntry, payload: CycleCreate) -> ConsumptionCycle:
        sequence = await self.session.scalar(
            select(func.coalesce(func.max(ConsumptionCycle.sequence_number), 0) + 1).where(
                ConsumptionCycle.library_entry_id == entry.id
            )
        )
        cycle = ConsumptionCycle(
            user_id=self.user_id,
            library_entry_id=entry.id,
            sequence_number=int(sequence or 1),
            state=CycleState.IN_PROGRESS,
            **payload.model_dump(),
        )
        self.session.add(cycle)
        await self.session.flush()
        return cycle

    async def update_cycle(self, cycle: ConsumptionCycle, payload: CycleUpdate) -> ConsumptionCycle:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(cycle, key, value)
        await self.session.flush()
        return cycle

    async def create_event(
        self, cycle: ConsumptionCycle, media_id: UUID, payload: ActivityCreate
    ) -> ActivityEvent:
        event = ActivityEvent(
            user_id=self.user_id,
            cycle_id=cycle.id,
            media_id=media_id,
            **payload.model_dump(),
        )
        self.session.add(event)
        if payload.progress_after is not None:
            cycle.progress_value = payload.progress_after
        await self.session.flush()
        return event

    async def create_standalone_event(
        self, media_id: UUID, payload: ActivityCreate
    ) -> ActivityEvent:
        event = ActivityEvent(
            user_id=self.user_id,
            cycle_id=None,
            media_id=media_id,
            **payload.model_dump(),
        )
        self.session.add(event)
        await self.session.flush()
        return event

    async def episode_belongs_to_media(self, episode_id: UUID, media_id: UUID) -> bool:
        value = await self.session.scalar(
            select(TVEpisode.id)
            .join(TVSeason, TVSeason.id == TVEpisode.season_id)
            .where(TVEpisode.id == episode_id, TVSeason.media_id == media_id)
        )
        return value is not None

    async def list_activity(self, *, offset: int = 0, limit: int = 100) -> list[ActivityEvent]:
        rows = await self.session.scalars(
            select(ActivityEvent)
            .where(ActivityEvent.user_id == self.user_id)
            .order_by(ActivityEvent.occurred_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(rows)

    async def year_counts(self, year: int) -> list[tuple[date, int]]:
        rows = await self.session.execute(
            select(ActivityEvent.occurred_on, func.count(ActivityEvent.id))
            .where(
                ActivityEvent.user_id == self.user_id,
                func.extract("year", ActivityEvent.occurred_on) == year,
            )
            .group_by(ActivityEvent.occurred_on)
            .order_by(ActivityEvent.occurred_on)
        )
        return [(row[0], int(row[1])) for row in rows]

    async def completed_in_year(self, year: int) -> int:
        value = await self.session.scalar(
            select(func.count(ActivityEvent.id)).where(
                ActivityEvent.user_id == self.user_id,
                ActivityEvent.kind == ActivityKind.COMPLETED,
                func.extract("year", ActivityEvent.occurred_on) == year,
            )
        )
        return int(value or 0)
