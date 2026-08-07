from typing import cast

from fastapi import APIRouter, Request, Response, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.api.dependencies import CurrentUserDep, SessionDep
from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.identity import Membership, Profile
from app.db.models.tracking import ActivityEvent, ConsumptionCycle, LibraryEntry
from app.schemas.accounts import ProfileRead, ProfileUpdate
from app.services.admin import AdminService

router = APIRouter(tags=["account"])


@router.get("/me", response_model=ProfileRead)
async def get_me(session: SessionDep, user: CurrentUserDep) -> ProfileRead:
    profile = await session.get(Profile, user.id)
    if profile is None:
        raise NotFoundError("PROFILE_NOT_FOUND", "The user profile does not exist.")
    return ProfileRead(
        user_id=profile.user_id,
        display_name=profile.display_name,
        timezone=profile.timezone,
        preferences=profile.preferences,
        role=user.role,
        created_at=profile.created_at,
    )


@router.patch("/me", response_model=ProfileRead)
async def update_me(
    payload: ProfileUpdate, session: SessionDep, user: CurrentUserDep
) -> ProfileRead:
    profile = await session.get(Profile, user.id)
    if profile is None:
        raise NotFoundError("PROFILE_NOT_FOUND", "The user profile does not exist.")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, key, value)
    await session.flush()
    return await get_me(session, user)


@router.post("/account/export")
async def export_account(session: SessionDep, user: CurrentUserDep) -> dict[str, object]:
    profile = await session.get(Profile, user.id)
    membership = await session.get(Membership, user.id)
    library = list(
        await session.scalars(select(LibraryEntry).where(LibraryEntry.user_id == user.id))
    )
    cycles = list(
        await session.scalars(select(ConsumptionCycle).where(ConsumptionCycle.user_id == user.id))
    )
    activity = list(
        await session.scalars(select(ActivityEvent).where(ActivityEvent.user_id == user.id))
    )
    return cast(
        dict[str, object],
        jsonable_encoder(
            {
                "profile": profile,
                "membership": membership,
                "library": library,
                "cycles": cycles,
                "activity": activity,
            }
        ),
    )


@router.delete("/account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(request: Request, session: SessionDep, user: CurrentUserDep) -> Response:
    membership = await session.get(Membership, user.id)
    if membership and membership.role.value == "owner":
        raise ConflictError(
            "OWNER_DELETE_FORBIDDEN", "Transfer ownership before deleting the owner."
        )
    service = AdminService(
        session, request.app.state.http_client, request.app.state.settings, user.id
    )
    await service.delete_auth_user(user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
