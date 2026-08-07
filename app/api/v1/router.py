from fastapi import APIRouter

from app.api.v1 import accounts, admin, arena, library, media, recommendations, reports, tracking

router = APIRouter()
router.include_router(accounts.router)
router.include_router(admin.router)
router.include_router(media.router)
router.include_router(library.router)
router.include_router(tracking.router)
router.include_router(arena.router)
router.include_router(reports.router)
router.include_router(recommendations.router)
