from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import MembershipRole, enum_values
from app.db.models.mixins import TimestampMixin


class Profile(TimestampMixin, Base):
    __tablename__ = "profiles"

    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata", nullable=False)
    preferences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)


class Membership(TimestampMixin, Base):
    __tablename__ = "memberships"

    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    role: Mapped[MembershipRole] = mapped_column(
        Enum(
            MembershipRole,
            name="membership_role",
            schema="app",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_log"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    actor_user_id: Mapped[UUID] = mapped_column(index=True)
    target_user_id: Mapped[UUID | None] = mapped_column(index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
