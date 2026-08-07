from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.db.models.enums import MembershipRole
from app.schemas.common import APIModel


class ProfileRead(APIModel):
    user_id: UUID
    display_name: str
    timezone: str
    preferences: dict[str, object]
    role: MembershipRole
    created_at: datetime


class ProfileUpdate(APIModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)
    preferences: dict[str, object] | None = None


class AdminUserCreate(APIModel):
    email: str
    password: str = Field(min_length=12, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    role: MembershipRole = MembershipRole.MEMBER


class PasswordReset(APIModel):
    password: str = Field(min_length=12, max_length=128)


class AdminUserRead(APIModel):
    user_id: UUID
    display_name: str
    role: MembershipRole
    active: bool
