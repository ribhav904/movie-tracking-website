from datetime import date, datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.db.models.enums import LibraryStatus
from app.schemas.common import APIModel


class LibraryCreate(APIModel):
    media_id: UUID
    status: LibraryStatus = LibraryStatus.PLANNED
    favorite: bool = False
    manual_rating: float | None = None
    notes: str | None = Field(default=None, max_length=20_000)

    @field_validator("manual_rating")
    @classmethod
    def validate_manual_rating(cls, value: float | None) -> float | None:
        if value is not None and (not 1 <= value <= 10 or value * 2 != round(value * 2)):
            raise ValueError("manual_rating must be from 1 to 10 in half-point steps")
        return value


class LibraryUpdate(APIModel):
    status: LibraryStatus | None = None
    favorite: bool | None = None
    manual_rating: float | None = None
    notes: str | None = Field(default=None, max_length=20_000)

    @field_validator("manual_rating")
    @classmethod
    def validate_manual_rating(cls, value: float | None) -> float | None:
        return LibraryCreate.validate_manual_rating(value)


class LibraryRead(APIModel):
    id: UUID
    media_id: UUID
    status: LibraryStatus
    favorite: bool
    manual_rating: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class ConsumptionCreate(APIModel):
    completed_on: date | None = None
    season_id: UUID | None = None
    rating: float | None = None
    notes: str | None = Field(default=None, max_length=20_000)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: float | None) -> float | None:
        if value is not None and (not 1 <= value <= 10 or value * 2 != round(value * 2)):
            raise ValueError("rating must be from 1 to 10 in half-point steps")
        return value


class ConsumptionUpdate(APIModel):
    completed_on: date | None = None
    rating: float | None = None
    notes: str | None = Field(default=None, max_length=20_000)

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, value: float | None) -> float | None:
        return ConsumptionCreate.validate_rating(value)


class ConsumptionRead(APIModel):
    id: UUID
    library_entry_id: UUID
    season_id: UUID | None
    sequence_number: int
    completed_on: date | None
    rating: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class SeasonSummary(APIModel):
    id: UUID
    season_number: int
    title: str | None
    air_date: date | None
    episode_count: int | None
    watched_count: int = 0
    latest_completed_on: date | None = None
    latest_rating: float | None = None


class HistoryItem(ConsumptionRead):
    media_id: UUID
    title: str
    media_type: str
    poster_url: str | None = None
    season_title: str | None = None
    season_number: int | None = None
