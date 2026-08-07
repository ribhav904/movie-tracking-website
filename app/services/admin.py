from uuid import UUID

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AppError, ConflictError, NotFoundError
from app.db.models.identity import AdminAuditLog, Membership, Profile
from app.schemas.accounts import AdminUserCreate, AdminUserRead


class AdminService:
    def __init__(
        self,
        session: AsyncSession,
        client: httpx.AsyncClient,
        settings: Settings,
        actor_id: UUID,
    ) -> None:
        self.session = session
        self.client = client
        self.settings = settings
        self.actor_id = actor_id

    @property
    def headers(self) -> dict[str, str]:
        return {
            "apikey": self.settings.SUPABASE_SECRET_KEY,
            "Authorization": f"Bearer {self.settings.SUPABASE_SECRET_KEY}",
            "Content-Type": "application/json",
        }

    async def list_users(self) -> list[AdminUserRead]:
        rows = await self.session.execute(
            select(Profile, Membership).join(Membership, Membership.user_id == Profile.user_id)
        )
        return [
            AdminUserRead(
                user_id=profile.user_id,
                display_name=profile.display_name,
                role=membership.role,
                active=membership.active,
            )
            for profile, membership in rows
        ]

    async def create_user(self, payload: AdminUserCreate) -> AdminUserRead:
        count = await self.session.scalar(
            select(func.count(Membership.user_id)).where(Membership.active.is_(True))
        )
        if int(count or 0) >= 3:
            raise ConflictError("MEMBERSHIP_LIMIT_REACHED", "At most three users may be active.")
        response = await self.client.post(
            f"{str(self.settings.SUPABASE_URL).rstrip('/')}/auth/v1/admin/users",
            headers=self.headers,
            json={
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
            },
        )
        if response.is_error:
            raise AppError(
                "SUPABASE_USER_CREATE_FAILED",
                "Supabase could not create the user.",
                status_code=502,
                details={"status": response.status_code},
            )
        user_id = UUID(response.json()["id"])
        self.session.add(Profile(user_id=user_id, display_name=payload.display_name))
        self.session.add(Membership(user_id=user_id, role=payload.role, active=True))
        self.session.add(
            AdminAuditLog(
                actor_user_id=self.actor_id,
                target_user_id=user_id,
                action="user.created",
                details={"email": payload.email, "role": payload.role.value},
            )
        )
        await self.session.flush()
        return AdminUserRead(
            user_id=user_id,
            display_name=payload.display_name,
            role=payload.role,
            active=True,
        )

    async def reset_password(self, user_id: UUID, password: str) -> None:
        await self._update_auth_user(user_id, {"password": password})
        self._audit(user_id, "user.password_reset")

    async def deactivate(self, user_id: UUID) -> None:
        membership = await self.session.get(Membership, user_id)
        if membership is None:
            raise NotFoundError("USER_NOT_FOUND", "The application user does not exist.")
        if membership.role.value == "owner":
            raise ConflictError("OWNER_DEACTIVATION_FORBIDDEN", "The owner cannot be deactivated.")
        membership.active = False
        await self._update_auth_user(user_id, {"ban_duration": "876000h"})
        self._audit(user_id, "user.deactivated")

    async def delete_auth_user(self, user_id: UUID) -> None:
        response = await self.client.delete(
            f"{str(self.settings.SUPABASE_URL).rstrip('/')}/auth/v1/admin/users/{user_id}",
            headers=self.headers,
        )
        if response.is_error:
            raise AppError(
                "SUPABASE_USER_DELETE_FAILED", "The account could not be deleted.", status_code=502
            )

    async def _update_auth_user(self, user_id: UUID, payload: dict[str, object]) -> None:
        response = await self.client.put(
            f"{str(self.settings.SUPABASE_URL).rstrip('/')}/auth/v1/admin/users/{user_id}",
            headers=self.headers,
            json=payload,
        )
        if response.is_error:
            raise AppError(
                "SUPABASE_USER_UPDATE_FAILED", "The account could not be updated.", status_code=502
            )

    def _audit(self, target_user_id: UUID, action: str) -> None:
        self.session.add(
            AdminAuditLog(
                actor_user_id=self.actor_id,
                target_user_id=target_user_id,
                action=action,
            )
        )
