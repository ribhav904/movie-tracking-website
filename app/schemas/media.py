from datetime import date
from uuid import UUID

from pydantic import Field

from app.db.models.enums import MediaProvider, MediaType
from app.schemas.common import APIModel


class PublicRating(APIModel):
    source: str
    value: float
    scale: float = 10.0
    count: int | None = None
    normalized_10: float


class MediaSummary(APIModel):
    media_id: UUID | None = None
    provider: MediaProvider
    external_id: str
    media_type: MediaType
    title: str
    description: str | None = None
    release_date: date | None = None
    poster_url: str | None = None
    genres: list[str] = Field(default_factory=list)
    public_rating: PublicRating | None = None


class MediaDetail(MediaSummary):
    original_title: str | None = None
    original_language: str | None = None
    backdrop_url: str | None = None
    credits: list[dict[str, str | int | None]] = Field(default_factory=list)
    extra: dict[str, object] = Field(default_factory=dict)


class MediaImportRequest(APIModel):
    provider: MediaProvider
    media_type: MediaType
    external_id: str
