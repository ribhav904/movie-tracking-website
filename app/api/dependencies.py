from collections.abc import AsyncIterator
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.auth import CurrentUser, SupabaseJWTVerifier
from app.core.exceptions import AppError, ForbiddenError
from app.db.models.identity import Membership
from app.db.session import set_current_user

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError("AUTHENTICATION_REQUIRED", "Authentication is required.", status_code=401)
    verifier: SupabaseJWTVerifier = request.app.state.jwt_verifier
    claims = await verifier.verify(credentials.credentials)
    try:
        user_id = UUID(str(claims["sub"]))
    except (KeyError, ValueError) as exc:
        raise AppError(
            "INVALID_ACCESS_TOKEN", "The token subject is invalid.", status_code=401
        ) from exc

    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session, session.begin():
        await set_current_user(session, user_id)
        membership = await session.scalar(
            select(Membership).where(Membership.user_id == user_id, Membership.active.is_(True))
        )
        if membership is None:
            raise ForbiddenError(
                "MEMBERSHIP_INACTIVE", "This account does not have application access."
            )
    return CurrentUser(id=user_id, role=membership.role, email=claims.get("email"))


async def get_db(
    request: Request, current_user: Annotated[CurrentUser, Depends(get_current_user)]
) -> AsyncIterator[AsyncSession]:
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as session, session.begin():
        await set_current_user(session, current_user.id, current_user.role.value)
        yield session


def require_owner(current_user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
    if current_user.role.value != "owner":
        raise ForbiddenError("OWNER_REQUIRED", "Owner access is required.")
    return current_user


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]
OwnerDep = Annotated[CurrentUser, Depends(require_owner)]
SessionDep = Annotated[AsyncSession, Depends(get_db)]
