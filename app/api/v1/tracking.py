from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.api.dependencies import CurrentUserDep, SessionDep
from app.db.models.enums import ActivityKind
from app.repositories.library import LibraryRepository
from app.repositories.tracking import TrackingRepository
from app.schemas.common import Page
from app.schemas.tracking import (
    ActivityCreate,
    ActivityRead,
    CycleComplete,
    CycleCreate,
    CycleRead,
    CycleUpdate,
)
from app.services.tracking import TrackingService

router = APIRouter(tags=["tracking"])


def _service(session: SessionDep, user: CurrentUserDep) -> TrackingService:
    return TrackingService(
        TrackingRepository(session, user.id), LibraryRepository(session, user.id)
    )


@router.post("/library/{entry_id}/cycles", response_model=CycleRead, status_code=201)
async def start_cycle(
    entry_id: UUID, payload: CycleCreate, session: SessionDep, user: CurrentUserDep
) -> CycleRead:
    return CycleRead.model_validate(await _service(session, user).start_cycle(entry_id, payload))


@router.patch("/cycles/{cycle_id}", response_model=CycleRead)
async def update_cycle(
    cycle_id: UUID, payload: CycleUpdate, session: SessionDep, user: CurrentUserDep
) -> CycleRead:
    return CycleRead.model_validate(await _service(session, user).update_cycle(cycle_id, payload))


@router.post("/cycles/{cycle_id}/events", response_model=ActivityRead, status_code=201)
async def add_event(
    cycle_id: UUID, payload: ActivityCreate, session: SessionDep, user: CurrentUserDep
) -> ActivityRead:
    return ActivityRead.model_validate(await _service(session, user).add_event(cycle_id, payload))


@router.post("/cycles/{cycle_id}/complete", response_model=ActivityRead, status_code=201)
async def complete_cycle(
    cycle_id: UUID, payload: CycleComplete, session: SessionDep, user: CurrentUserDep
) -> ActivityRead:
    activity = ActivityCreate(
        kind=ActivityKind.COMPLETED,
        occurred_at=payload.occurred_at,
        occurred_on=payload.occurred_on,
        notes=payload.notes,
    )
    return ActivityRead.model_validate(
        await _service(session, user).complete(
            cycle_id, occurred_on=payload.occurred_on, payload=activity
        )
    )


@router.post("/tv/episodes/{episode_id}/viewings", response_model=ActivityRead, status_code=201)
async def log_episode_viewing(
    episode_id: UUID,
    cycle_id: UUID,
    payload: ActivityCreate,
    session: SessionDep,
    user: CurrentUserDep,
) -> ActivityRead:
    activity = payload.model_copy(
        update={"kind": ActivityKind.EPISODE_WATCHED, "episode_id": episode_id}
    )
    return ActivityRead.model_validate(await _service(session, user).add_event(cycle_id, activity))


@router.get("/activity", response_model=Page[ActivityRead])
async def list_activity(
    session: SessionDep,
    user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> Page[ActivityRead]:
    items = await TrackingRepository(session, user.id).list_activity(offset=offset, limit=limit)
    return Page(
        items=[ActivityRead.model_validate(item) for item in items],
        next_cursor=str(offset + limit) if len(items) == limit else None,
    )
