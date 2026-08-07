from uuid import UUID

from fastapi import APIRouter, Request, status

from app.api.dependencies import OwnerDep, SessionDep
from app.schemas.accounts import AdminUserCreate, AdminUserRead, PasswordReset
from app.schemas.common import Message
from app.services.admin import AdminService

router = APIRouter(prefix="/admin/users", tags=["admin"])


def _service(request: Request, session: SessionDep, owner: OwnerDep) -> AdminService:
    return AdminService(
        session, request.app.state.http_client, request.app.state.settings, owner.id
    )


@router.get("", response_model=list[AdminUserRead])
async def list_users(request: Request, session: SessionDep, owner: OwnerDep) -> list[AdminUserRead]:
    return await _service(request, session, owner).list_users()


@router.post("", response_model=AdminUserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: AdminUserCreate, request: Request, session: SessionDep, owner: OwnerDep
) -> AdminUserRead:
    return await _service(request, session, owner).create_user(payload)


@router.post("/{user_id}/reset-password", response_model=Message)
async def reset_password(
    user_id: UUID,
    payload: PasswordReset,
    request: Request,
    session: SessionDep,
    owner: OwnerDep,
) -> Message:
    await _service(request, session, owner).reset_password(user_id, payload.password)
    return Message(message="Password reset successfully.")


@router.post("/{user_id}/deactivate", response_model=Message)
async def deactivate_user(
    user_id: UUID, request: Request, session: SessionDep, owner: OwnerDep
) -> Message:
    await _service(request, session, owner).deactivate(user_id)
    return Message(message="User deactivated successfully.")
