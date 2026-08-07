from fastapi import APIRouter

from app.api.dependencies import CurrentUserDep, SessionDep
from app.repositories.library import LibraryRepository
from app.repositories.tracking import TrackingRepository
from app.schemas.reports import ReportSummary, YearReport
from app.services.reports import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])


def _service(session: SessionDep, user: CurrentUserDep) -> ReportService:
    return ReportService(TrackingRepository(session, user.id), LibraryRepository(session, user.id))


@router.get("/year/{year}", response_model=YearReport)
async def year_report(year: int, session: SessionDep, user: CurrentUserDep) -> YearReport:
    return await _service(session, user).year(year)


@router.get("/summary", response_model=ReportSummary)
async def report_summary(session: SessionDep, user: CurrentUserDep) -> ReportSummary:
    return await _service(session, user).summary()
