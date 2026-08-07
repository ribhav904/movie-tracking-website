from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.api.error_handlers import install_error_handlers
from app.api.v1.router import router as api_router
from app.core.auth import SupabaseJWTVerifier
from app.core.config import Settings, get_settings
from app.core.logging import configure_logging
from app.db.engine import create_database_engine
from app.db.models.enums import MediaProvider
from app.db.session import create_session_factory
from app.integrations.google_books import GoogleBooksClient
from app.integrations.igdb import IGDBClient
from app.integrations.open_library import OpenLibraryClient
from app.integrations.registry import ProviderRegistry
from app.integrations.tmdb import TMDBClient


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.LOG_LEVEL)
    logger = structlog.get_logger()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_database_engine(settings)
        client = httpx.AsyncClient(timeout=settings.PROVIDER_TIMEOUT_SECONDS)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
        app.state.http_client = client
        app.state.settings = settings
        app.state.jwt_verifier = SupabaseJWTVerifier(settings, client)
        app.state.providers = ProviderRegistry(
            {
                MediaProvider.TMDB: TMDBClient(client, settings.TMDB_ACCESS_TOKEN),
                MediaProvider.IGDB: IGDBClient(
                    client, settings.IGDB_CLIENT_ID, settings.IGDB_CLIENT_SECRET
                ),
                MediaProvider.GOOGLE_BOOKS: GoogleBooksClient(
                    client, settings.GOOGLE_BOOKS_API_KEY
                ),
                MediaProvider.OPEN_LIBRARY: OpenLibraryClient(
                    client, settings.OPEN_LIBRARY_CONTACT
                ),
            }
        )
        logger.info("application_started", environment=settings.APP_ENV)
        try:
            yield
        finally:
            await client.aclose()
            await engine.dispose()
            logger.info("application_stopped")

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/openapi.json",
        docs_url="/docs",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Request-ID"],
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get("X-Request-ID", str(uuid4()))[:128]
        request.state.request_id = request_id
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/health/live", tags=["system"])
    async def liveness() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/health/ready", tags=["system"])
    async def readiness(request: Request) -> JSONResponse:
        try:
            async with request.app.state.engine.connect() as connection:
                await connection.execute(text("select 1"))
            return JSONResponse({"status": "ready"})
        except Exception:
            logger.exception("readiness_check_failed")
            return JSONResponse({"status": "not_ready"}, status_code=503)

    app.include_router(api_router, prefix=settings.API_PREFIX)
    install_error_handlers(app)
    return app


app = create_app()
