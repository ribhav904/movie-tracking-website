from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.models.enums import MediaProvider, MediaType, enum_values
from app.db.models.mixins import TimestampMixin


class MediaItem(TimestampMixin, Base):
    __tablename__ = "media_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    media_type: Mapped[MediaType] = mapped_column(
        Enum(MediaType, name="media_type", schema="app", values_callable=enum_values),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False, index=True)
    original_title: Mapped[str | None] = mapped_column(String(500))
    description: Mapped[str | None] = mapped_column(Text)
    release_date: Mapped[date | None] = mapped_column(Date)
    original_language: Mapped[str | None] = mapped_column(String(20))
    poster_url: Mapped[str | None] = mapped_column(Text)
    backdrop_url: Mapped[str | None] = mapped_column(Text)
    public_rating: Mapped[float | None] = mapped_column(Numeric(4, 2))
    public_rating_count: Mapped[int | None] = mapped_column(Integer)
    public_rating_source: Mapped[str | None] = mapped_column(String(40))
    cached_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MediaSource(Base):
    __tablename__ = "media_sources"
    __table_args__ = (
        UniqueConstraint("provider", "media_type", "external_id", name="uq_media_source"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    provider: Mapped[MediaProvider] = mapped_column(
        Enum(
            MediaProvider,
            name="media_provider",
            schema="app",
            values_callable=enum_values,
        ),
        nullable=False,
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
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text)
    raw_rating: Mapped[float | None] = mapped_column(Numeric(8, 3))
    raw_rating_scale: Mapped[float | None] = mapped_column(Numeric(8, 3))
    raw_rating_count: Mapped[int | None] = mapped_column(Integer)
    normalized_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class MovieDetails(Base):
    __tablename__ = "movie_details"

    media_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.media_items.id", ondelete="CASCADE"), primary_key=True
    )
    runtime_minutes: Mapped[int | None] = mapped_column(Integer)


class TVDetails(Base):
    __tablename__ = "tv_details"

    media_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.media_items.id", ondelete="CASCADE"), primary_key=True
    )
    status: Mapped[str | None] = mapped_column(String(80))
    season_count: Mapped[int | None] = mapped_column(Integer)
    episode_count: Mapped[int | None] = mapped_column(Integer)


class TVSeason(Base):
    __tablename__ = "tv_seasons"
    __table_args__ = (UniqueConstraint("media_id", "season_number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    season_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(String(500))
    air_date: Mapped[date | None] = mapped_column(Date)
    episode_count: Mapped[int | None] = mapped_column(Integer)


class TVEpisode(Base):
    __tablename__ = "tv_episodes"
    __table_args__ = (UniqueConstraint("season_id", "episode_number"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    season_id: Mapped[UUID] = mapped_column(ForeignKey("app.tv_seasons.id", ondelete="CASCADE"))
    episode_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    air_date: Mapped[date | None] = mapped_column(Date)
    runtime_minutes: Mapped[int | None] = mapped_column(Integer)


class GameDetails(Base):
    __tablename__ = "game_details"

    media_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.media_items.id", ondelete="CASCADE"), primary_key=True
    )
    platforms: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    companies: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    game_modes: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)


class BookDetails(Base):
    __tablename__ = "book_details"

    media_id: Mapped[UUID] = mapped_column(
        ForeignKey("app.media_items.id", ondelete="CASCADE"), primary_key=True
    )
    isbn_10: Mapped[str | None] = mapped_column(String(10), index=True)
    isbn_13: Mapped[str | None] = mapped_column(String(13), index=True)
    authors: Mapped[list[str]] = mapped_column(ARRAY(String), default=list, nullable=False)
    publisher: Mapped[str | None] = mapped_column(String(300))
    page_count: Mapped[int | None] = mapped_column(Integer)
    edition: Mapped[str | None] = mapped_column(String(200))


class MediaGenre(Base):
    __tablename__ = "media_genres"
    __table_args__ = (UniqueConstraint("media_id", "name"),)

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120), nullable=False, index=True)


class MediaCredit(Base):
    __tablename__ = "media_credits"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    media_id: Mapped[UUID] = mapped_column(ForeignKey("app.media_items.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(300), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    character: Mapped[str | None] = mapped_column(String(300))
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
