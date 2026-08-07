from app.repositories.library import LibraryRepository
from app.repositories.tracking import TrackingRepository
from app.schemas.reports import DailyActivity, ReportSummary, YearReport


class ReportService:
    def __init__(
        self, tracking_repository: TrackingRepository, library_repository: LibraryRepository
    ) -> None:
        self.tracking_repository = tracking_repository
        self.library_repository = library_repository

    async def year(self, year: int) -> YearReport:
        counts = await self.tracking_repository.year_counts(year)
        return YearReport(
            year=year,
            media_type=None,
            total_events=sum(count for _, count in counts),
            active_days=len(counts),
            completed_items=await self.tracking_repository.completed_in_year(year),
            calendar=[DailyActivity(date=day, count=count) for day, count in counts],
        )

    async def summary(self) -> ReportSummary:
        total, completed, favorites, average = await self.library_repository.stats()
        return ReportSummary(
            library_items=total,
            completed_items=completed,
            favorites=favorites,
            average_manual_rating=average,
        )
