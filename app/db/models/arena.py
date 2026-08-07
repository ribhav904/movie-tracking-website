from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import ArenaOutcome, MediaType, enum_values
from app.db.models.mixins import TimestampMixin


class ArenaRating(TimestampMixin, Base):
    __tablename__ = "arena_ratings"
    __table_args__ = (UniqueConstraint("user_id", "media_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    media_type: Mapped[MediaType] = mapped_column(
        Enum(
            MediaType,
            name="media_type",
            schema="app",
            create_type=False,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    elo: Mapped[float] = mapped_column(Float, default=1500.0, nullable=False)
    matches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    wins: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    losses: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    ties: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class ArenaComparison(Base):
    __tablename__ = "arena_comparisons"
    __table_args__ = (
        UniqueConstraint("user_id", "media_low_id", "media_high_id", name="uq_arena_pair"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_arena_idempotency"),
        CheckConstraint("media_low_id < media_high_id", name="ordered_pair"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    media_type: Mapped[MediaType] = mapped_column(
        Enum(
            MediaType,
            name="media_type",
            schema="app",
            create_type=False,
            values_callable=enum_values,
        ),
        nullable=False,
    )
    media_low_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.media_items.id", ondelete="RESTRICT")
    )
    media_high_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.media_items.id", ondelete="RESTRICT")
    )
    left_media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id"))
    right_media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id"))
    outcome: Mapped[ArenaOutcome] = mapped_column(
        Enum(
            ArenaOutcome,
            name="arena_outcome",
            schema="app",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    left_elo_before: Mapped[float] = mapped_column(Float, nullable=False)
    right_elo_before: Mapped[float] = mapped_column(Float, nullable=False)
    left_elo_after: Mapped[float] = mapped_column(Float, nullable=False)
    right_elo_after: Mapped[float] = mapped_column(Float, nullable=False)
    left_k_factor: Mapped[int] = mapped_column(Integer, nullable=False)
    right_k_factor: Mapped[int] = mapped_column(Integer, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
