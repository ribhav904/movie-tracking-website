from datetime import date, datetime
from uuid import UUID

from pydantic import Field, field_validator

from app.db.models.enums import ActivityKind, CycleState, LibraryStatus
from app.schemas.common import APIModel


class LibraryCreate(APIModel):
    media_id: UUID
    status: LibraryStatus = LibraryStatus.PLANNED
    favorite: bool = False
    manual_rating: float | None = None
    notes: str | None = Field(default=None, max_length=20_000)

    @field_validator("manual_rating")
    @classmethod
    def validate_rating(cls, value: float | None) -> float | None:
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
    def validate_rating(cls, value: float | None) -> float | None:
        return LibraryCreate.validate_rating(value)


class LibraryRead(APIModel):
    id: UUID
    media_id: UUID
    status: LibraryStatus
    favorite: bool
    manual_rating: float | None
    notes: str | None
    created_at: datetime
    updated_at: datetime


class CycleCreate(APIModel):
    started_on: date
    progress_value: float | None = Field(default=None, ge=0)
    progress_unit: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=20_000)


class CycleUpdate(APIModel):
    state: CycleState | None = None
    progress_value: float | None = Field(default=None, ge=0)
    progress_unit: str | None = Field(default=None, max_length=40)
    notes: str | None = Field(default=None, max_length=20_000)


class CycleRead(APIModel):
    id: UUID
    library_entry_id: UUID
    sequence_number: int
    state: CycleState
    started_on: date
    completed_on: date | None
    progress_value: float | None
    progress_unit: str | None
    notes: str | None


class CycleComplete(APIModel):
    occurred_at: datetime
    occurred_on: date
    notes: str | None = Field(default=None, max_length=20_000)


class ActivityCreate(APIModel):
    kind: ActivityKind
    occurred_at: datetime
    occurred_on: date
    amount: float | None = Field(default=None, ge=0)
    duration_minutes: int | None = Field(default=None, ge=0, le=100_000)
    progress_after: float | None = Field(default=None, ge=0)
    episode_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=20_000)


class ActivityRead(APIModel):
    id: UUID
    cycle_id: UUID | None
    media_id: UUID
    episode_id: UUID | None
    kind: ActivityKind
    occurred_at: datetime
    occurred_on: date
    amount: float | None
    duration_minutes: int | None
    progress_after: float | None
    notes: str | None
