from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import CurrentUserDep, SessionDep
from app.repositories.catalog import CatalogRepository
from app.repositories.library import LibraryRepository
from app.repositories.tracking import TrackingRepository
from app.schemas.common import Page
from app.schemas.tracking import (
    ConsumptionCreate,
    ConsumptionRead,
    ConsumptionUpdate,
    HistoryItem,
)
from app.services.tracking import TrackingService

router = APIRouter(tags=["tracking"])


def _service(session: SessionDep, user: CurrentUserDep) -> TrackingService:
    return TrackingService(
        TrackingRepository(session, user.id),
        LibraryRepository(session, user.id),
        CatalogRepository(session),
    )


@router.get("/library/{entry_id}/consumptions", response_model=list[ConsumptionRead])
async def list_consumptions(
    entry_id: UUID, session: SessionDep, user: CurrentUserDep
) -> list[ConsumptionRead]:
    records = await _service(session, user).list_records(entry_id)
    return [ConsumptionRead.model_validate(record) for record in records]


@router.post(
    "/library/{entry_id}/consumptions",
    response_model=ConsumptionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_consumption(
    entry_id: UUID, payload: ConsumptionCreate, session: SessionDep, user: CurrentUserDep
) -> ConsumptionRead:
    record = await _service(session, user).record(entry_id, payload)
    return ConsumptionRead.model_validate(record)


@router.patch("/consumptions/{record_id}", response_model=ConsumptionRead)
async def update_consumption(
    record_id: UUID, payload: ConsumptionUpdate, session: SessionDep, user: CurrentUserDep
) -> ConsumptionRead:
    record = await _service(session, user).update(record_id, payload)
    return ConsumptionRead.model_validate(record)


@router.delete("/consumptions/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_consumption(
    record_id: UUID, session: SessionDep, user: CurrentUserDep
) -> Response:
    await _service(session, user).delete(record_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/history", response_model=Page[HistoryItem])
async def list_history(
    session: SessionDep,
    user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=200)] = 100,
) -> Page[HistoryItem]:
    items = await _service(session, user).history(offset=offset, limit=limit)
    return Page(items=items, next_cursor=str(offset + limit) if len(items) == limit else None)
