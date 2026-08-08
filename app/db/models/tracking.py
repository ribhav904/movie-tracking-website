from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import ActivityKind, CycleState, LibraryStatus, enum_values
from app.db.models.mixins import TimestampMixin


class LibraryEntry(TimestampMixin, Base):
    __tablename__ = "library_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "media_id"),
        CheckConstraint(
            "manual_rating is null or (manual_rating >= 1 and manual_rating <= 10 and "
            "manual_rating * 2 = trunc(manual_rating * 2))",
            name="manual_rating_half_steps",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    status: Mapped[LibraryStatus] = mapped_column(
        Enum(
            LibraryStatus,
            name="library_status",
            schema="app",
            values_callable=enum_values,
        ),
        nullable=False,
    )
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    manual_rating: Mapped[float | None] = mapped_column(Numeric(3, 1))
    notes: Mapped[str | None] = mapped_column(Text)


class ConsumptionRecord(TimestampMixin, Base):
    __tablename__ = "consumption_records"
    __table_args__ = (
        UniqueConstraint("library_entry_id", "sequence_number"),
        CheckConstraint(
            "rating is null or (rating >= 1 and rating <= 10 and rating * 2 = trunc(rating * 2))",
            name="consumption_rating_half_steps",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    library_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.library_entries.id", ondelete="CASCADE"), index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    completed_on: Mapped[date | None] = mapped_column(Date)
    season_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("app.tv_seasons.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[float | None] = mapped_column(Numeric(3, 1))
    notes: Mapped[str | None] = mapped_column(Text)


class LegacyConsumptionCycle(TimestampMixin, Base):
    """Compatibility model for the already-merged initial migration only."""

    __tablename__ = "consumption_cycles"
    __table_args__ = (UniqueConstraint("library_entry_id", "sequence_number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    library_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.library_entries.id", ondelete="CASCADE"), index=True
    )
    sequence_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[CycleState] = mapped_column(
        Enum(CycleState, name="cycle_state", schema="app", values_callable=enum_values),
        nullable=False,
    )
    started_on: Mapped[date] = mapped_column(Date, nullable=False)
    completed_on: Mapped[date | None] = mapped_column(Date)
    progress_value: Mapped[float | None] = mapped_column(Numeric(10, 2))
    progress_unit: Mapped[str | None] = mapped_column(String(40))
    notes: Mapped[str | None] = mapped_column(Text)


class LegacyActivityEvent(Base):
    """Compatibility model for the already-merged initial migration only."""

    __tablename__ = "activity_events"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    cycle_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("app.consumption_cycles.id", ondelete="CASCADE"), index=True
    )
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    episode_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("app.tv_episodes.id", ondelete="SET NULL")
    )
    kind: Mapped[ActivityKind] = mapped_column(
        Enum(ActivityKind, name="activity_kind", schema="app", values_callable=enum_values),
        nullable=False,
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    occurred_on: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    amount: Mapped[float | None] = mapped_column(Numeric(10, 2))
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    progress_after: Mapped[float | None] = mapped_column(Numeric(10, 2))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class CustomList(TimestampMixin, Base):
    __tablename__ = "custom_lists"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class CustomListItem(Base):
    __tablename__ = "custom_list_items"
    __table_args__ = (UniqueConstraint("list_id", "media_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    list_id: Mapped[UUID] = mapped_column(ForeignKey("app.custom_lists.id", ondelete="CASCADE"))
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)


class LibraryEntryTag(Base):
    __tablename__ = "library_entry_tags"
    __table_args__ = (UniqueConstraint("library_entry_id", "tag_id"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.profiles.user_id", ondelete="CASCADE"), index=True
    )
    library_entry_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.library_entries.id", ondelete="CASCADE")
    )
    tag_id: Mapped[UUID] = mapped_column(ForeignKey("app.tags.id", ondelete="CASCADE"))
