from fastapi import APIRouter, Request

from app.api.dependencies import CurrentUserDep, SessionDep
from app.db.models.enums import MediaType
from app.repositories.catalog import CatalogRepository
from app.repositories.recommendations import RecommendationRepository
from app.schemas.common import Page
from app.schemas.media import MediaSummary
from app.services.media import MediaService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{media_type}", response_model=Page[MediaSummary])
async def recommendations(
    media_type: MediaType,
    request: Request,
    session: SessionDep,
    user: CurrentUserDep,
) -> Page[MediaSummary]:
    rows = await RecommendationRepository(session, user.id).candidates(media_type)
    media_service = MediaService(request.app.state.providers, CatalogRepository(session))
    return Page(items=[await media_service.by_id(row.id) for row in rows])
