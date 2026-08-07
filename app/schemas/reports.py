from datetime import date

from app.db.models.enums import MediaType
from app.schemas.common import APIModel


class DailyActivity(APIModel):
    date: date
    count: int


class YearReport(APIModel):
    year: int
    media_type: MediaType | None
    total_events: int
    active_days: int
    completed_items: int
    calendar: list[DailyActivity]


class ReportSummary(APIModel):
    library_items: int
    completed_items: int
    favorites: int
    average_manual_rating: float | None
