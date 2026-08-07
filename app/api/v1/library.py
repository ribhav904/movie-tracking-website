from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response, status

from app.api.dependencies import CurrentUserDep, SessionDep
from app.repositories.catalog import CatalogRepository
from app.repositories.library import LibraryRepository
from app.schemas.common import Page
from app.schemas.tracking import LibraryCreate, LibraryRead, LibraryUpdate
from app.services.library import LibraryService

router = APIRouter(prefix="/library", tags=["library"])


def _service(session: SessionDep, user: CurrentUserDep) -> LibraryService:
    return LibraryService(LibraryRepository(session, user.id), CatalogRepository(session))


@router.get("", response_model=Page[LibraryRead])
async def list_library(
    session: SessionDep,
    user: CurrentUserDep,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> Page[LibraryRead]:
    items = await LibraryRepository(session, user.id).list(offset=offset, limit=limit)
    return Page(
        items=[LibraryRead.model_validate(item) for item in items],
        next_cursor=str(offset + limit) if len(items) == limit else None,
    )


@router.post("", response_model=LibraryRead, status_code=status.HTTP_201_CREATED)
async def create_library_entry(
    payload: LibraryCreate, session: SessionDep, user: CurrentUserDep
) -> LibraryRead:
    return LibraryRead.model_validate(await _service(session, user).create(payload))


@router.get("/{entry_id}", response_model=LibraryRead)
async def get_library_entry(
    entry_id: UUID, session: SessionDep, user: CurrentUserDep
) -> LibraryRead:
    return LibraryRead.model_validate(await _service(session, user).get(entry_id))


@router.patch("/{entry_id}", response_model=LibraryRead)
async def update_library_entry(
    entry_id: UUID, payload: LibraryUpdate, session: SessionDep, user: CurrentUserDep
) -> LibraryRead:
    return LibraryRead.model_validate(await _service(session, user).update(entry_id, payload))


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_library_entry(
    entry_id: UUID, session: SessionDep, user: CurrentUserDep
) -> Response:
    await _service(session, user).delete(entry_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
