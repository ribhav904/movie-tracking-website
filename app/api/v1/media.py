from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request

from app.api.dependencies import CurrentUserDep, SessionDep
from app.db.models.enums import MediaProvider, MediaType
from app.repositories.catalog import CatalogRepository
from app.repositories.library import LibraryRepository
from app.repositories.tracking import TrackingRepository
from app.schemas.common import Page
from app.schemas.media import MediaDetail, MediaImportRequest, MediaSummary
from app.schemas.tracking import SeasonSummary
from app.services.media import MediaService
from app.services.tracking import TrackingService

router = APIRouter(prefix="/media", tags=["media"])


def _service(request: Request, session: SessionDep) -> MediaService:
    return MediaService(request.app.state.providers, CatalogRepository(session))


def _tracking_service(session: SessionDep, user: CurrentUserDep) -> TrackingService:
    return TrackingService(
        TrackingRepository(session, user.id),
        LibraryRepository(session, user.id),
        CatalogRepository(session),
    )


@router.get("/search", response_model=Page[MediaSummary])
async def search_media(
    request: Request,
    session: SessionDep,
    _user: CurrentUserDep,
    query: Annotated[str, Query(min_length=1, max_length=200)],
    media_type: MediaType,
    page: Annotated[int, Query(ge=1, le=100)] = 1,
) -> Page[MediaSummary]:
    items = await _service(request, session).search(query, media_type, page)
    return Page(items=items, next_cursor=str(page + 1) if len(items) == 20 else None)


@router.get("/discover", response_model=Page[MediaSummary])
async def discover_media(
    request: Request,
    session: SessionDep,
    _user: CurrentUserDep,
    media_type: MediaType,
    page: Annotated[int, Query(ge=1, le=100)] = 1,
) -> Page[MediaSummary]:
    items = await _service(request, session).discover(media_type, page)
    return Page(items=items, next_cursor=str(page + 1) if len(items) == 20 else None)


@router.get("/provider/{provider}/{external_id}", response_model=MediaDetail)
async def provider_detail(
    provider: MediaProvider,
    external_id: str,
    media_type: MediaType,
    request: Request,
    session: SessionDep,
    _user: CurrentUserDep,
) -> MediaDetail:
    return await _service(request, session).detail(provider, media_type, external_id)


@router.post("/import", response_model=MediaDetail)
async def import_media(
    payload: MediaImportRequest,
    request: Request,
    session: SessionDep,
    _user: CurrentUserDep,
) -> MediaDetail:
    return await _service(request, session).detail(
        payload.provider, payload.media_type, payload.external_id
    )


@router.get("/{media_id}", response_model=MediaSummary)
async def get_media(
    media_id: UUID,
    request: Request,
    session: SessionDep,
    _user: CurrentUserDep,
) -> MediaSummary:
    return await _service(request, session).by_id(media_id)


@router.get("/{media_id}/details", response_model=MediaDetail)
async def get_media_detail(
    media_id: UUID,
    request: Request,
    session: SessionDep,
    _user: CurrentUserDep,
) -> MediaDetail:
    return await _service(request, session).detail_by_id(media_id)


@router.get("/{media_id}/seasons", response_model=list[SeasonSummary])
async def list_tv_seasons(
    media_id: UUID, session: SessionDep, user: CurrentUserDep
) -> list[SeasonSummary]:
    return await _tracking_service(session, user).season_summaries(media_id)


@router.get("/{media_id}/recommendations", response_model=Page[MediaSummary])
async def similar_media(
    media_id: UUID,
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
) -> Page[MediaSummary]:
    # The personalized recommender is used as a useful content-based fallback in v1.
    item = await _service(request, session).by_id(media_id)
    from app.repositories.recommendations import RecommendationRepository

    candidates = await RecommendationRepository(session, user.id).candidates(item.media_type)
    service = _service(request, session)
    return Page(items=[await service.by_id(candidate.id) for candidate in candidates])
