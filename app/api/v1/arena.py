from typing import Annotated, Literal

from fastapi import APIRouter, Header, Query

from app.api.dependencies import CurrentUserDep, SessionDep
from app.db.models.enums import MediaType
from app.repositories.arena import ArenaRepository
from app.schemas.arena import (
    ArenaComparisonCreate,
    ArenaComparisonRead,
    ArenaMatchup,
    ArenaRanking,
)
from app.services.arena import ArenaService

router = APIRouter(prefix="/arena", tags=["arena"])


def _service(session: SessionDep, user: CurrentUserDep) -> ArenaService:
    return ArenaService(ArenaRepository(session, user.id))


@router.get("/{media_type}/matchup", response_model=ArenaMatchup)
async def get_matchup(
    media_type: MediaType,
    session: SessionDep,
    user: CurrentUserDep,
    mode: Literal["guided", "random"] = Query(default="guided"),
) -> ArenaMatchup:
    return await _service(session, user).matchup(media_type, mode)


@router.post("/{media_type}/comparisons", response_model=ArenaComparisonRead, status_code=201)
async def record_comparison(
    media_type: MediaType,
    payload: ArenaComparisonCreate,
    session: SessionDep,
    user: CurrentUserDep,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=8, max_length=128)],
) -> ArenaComparisonRead:
    row = await _service(session, user).record(
        media_type,
        payload.left_media_id,
        payload.right_media_id,
        payload.outcome,
        idempotency_key,
    )
    return ArenaComparisonRead.model_validate(row)


@router.get("/{media_type}/rankings", response_model=list[ArenaRanking])
async def get_rankings(
    media_type: MediaType, session: SessionDep, user: CurrentUserDep
) -> list[ArenaRanking]:
    return await _service(session, user).rankings(media_type)
