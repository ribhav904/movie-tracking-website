from datetime import date
from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.enums import ActivityKind, CycleState, LibraryStatus
from app.db.models.tracking import ActivityEvent, ConsumptionCycle
from app.repositories.library import LibraryRepository
from app.repositories.tracking import TrackingRepository
from app.schemas.tracking import ActivityCreate, CycleCreate, CycleUpdate


class TrackingService:
    def __init__(
        self, repository: TrackingRepository, library_repository: LibraryRepository
    ) -> None:
        self.repository = repository
        self.library_repository = library_repository

    async def start_cycle(self, entry_id: UUID, payload: CycleCreate) -> ConsumptionCycle:
        entry = await self.library_repository.get(entry_id)
        if entry is None:
            raise NotFoundError("LIBRARY_ENTRY_NOT_FOUND", "The library entry does not exist.")
        entry.status = LibraryStatus.IN_PROGRESS
        return await self.repository.create_cycle(entry, payload)

    async def update_cycle(self, cycle_id: UUID, payload: CycleUpdate) -> ConsumptionCycle:
        cycle = await self._cycle(cycle_id)
        if cycle.state == CycleState.COMPLETED:
            raise ConflictError("CYCLE_ALREADY_COMPLETED", "A completed cycle cannot be edited.")
        return await self.repository.update_cycle(cycle, payload)

    async def add_event(self, cycle_id: UUID, payload: ActivityCreate) -> ActivityEvent:
        cycle = await self._cycle(cycle_id)
        if cycle.state == CycleState.COMPLETED:
            raise ConflictError(
                "CYCLE_ALREADY_COMPLETED", "A completed cycle cannot receive events."
            )
        entry = await self.library_repository.get(cycle.library_entry_id)
        if entry is None:
            raise NotFoundError("LIBRARY_ENTRY_NOT_FOUND", "The library entry does not exist.")
        if payload.episode_id is not None and not await self.repository.episode_belongs_to_media(
            payload.episode_id, entry.media_id
        ):
            raise NotFoundError(
                "TV_EPISODE_NOT_FOUND",
                "The episode does not belong to this cycle's media item.",
            )
        return await self.repository.create_event(cycle, entry.media_id, payload)

    async def add_entry_event(self, entry_id: UUID, payload: ActivityCreate) -> ActivityEvent:
        entry = await self.library_repository.get(entry_id)
        if entry is None:
            raise NotFoundError("LIBRARY_ENTRY_NOT_FOUND", "The library entry does not exist.")

        if payload.kind in {ActivityKind.NOTE, ActivityKind.RATED}:
            return await self.repository.create_standalone_event(entry.media_id, payload)

        cycle = await self.repository.get_active_cycle(entry_id)
        if cycle is None:
            cycle = await self.start_cycle(entry_id, CycleCreate(started_on=payload.occurred_on))

        if payload.kind == ActivityKind.COMPLETED:
            return await self.complete(cycle.id, occurred_on=payload.occurred_on, payload=payload)
        return await self.add_event(cycle.id, payload)

    async def complete(
        self, cycle_id: UUID, *, occurred_on: date, payload: ActivityCreate
    ) -> ActivityEvent:
        cycle = await self._cycle(cycle_id)
        if cycle.state == CycleState.COMPLETED:
            raise ConflictError("CYCLE_ALREADY_COMPLETED", "This cycle is already complete.")
        entry = await self.library_repository.get(cycle.library_entry_id)
        if entry is None:
            raise NotFoundError("LIBRARY_ENTRY_NOT_FOUND", "The library entry does not exist.")
        cycle.state = CycleState.COMPLETED
        cycle.completed_on = occurred_on
        entry.status = LibraryStatus.COMPLETED
        completion = payload.model_copy(
            update={"kind": ActivityKind.COMPLETED, "occurred_on": occurred_on}
        )
        return await self.repository.create_event(cycle, entry.media_id, completion)

    async def _cycle(self, cycle_id: UUID) -> ConsumptionCycle:
        cycle = await self.repository.get_cycle(cycle_id)
        if cycle is None:
            raise NotFoundError("CYCLE_NOT_FOUND", "The consumption cycle does not exist.")
        return cycle
