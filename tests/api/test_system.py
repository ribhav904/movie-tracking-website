from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def settings() -> Settings:
    return Settings(
        DATABASE_URL="postgresql+psycopg://user:password@localhost:5432/postgres",
        SUPABASE_URL="https://example.supabase.co",
        SUPABASE_PUBLISHABLE_KEY="publishable",
        SUPABASE_SECRET_KEY="secret",
        OPEN_LIBRARY_CONTACT="test@example.com",
    )


def test_liveness() -> None:
    with TestClient(create_app(settings())) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Request-ID"]


def test_protected_endpoint_requires_bearer_token() -> None:
    with TestClient(create_app(settings())) as client:
        response = client.get("/api/v1/library")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_openapi_contains_primary_routes() -> None:
    with TestClient(create_app(settings())) as client:
        document = client.get("/openapi.json").json()
    expected_paths = {
        "/health/live",
        "/health/ready",
        "/api/v1/me",
        "/api/v1/account/export",
        "/api/v1/account",
        "/api/v1/admin/users",
        "/api/v1/admin/users/{user_id}/reset-password",
        "/api/v1/admin/users/{user_id}/deactivate",
        "/api/v1/media/search",
        "/api/v1/media/discover",
        "/api/v1/media/provider/{provider}/{external_id}",
        "/api/v1/media/import",
        "/api/v1/media/{media_id}",
        "/api/v1/media/{media_id}/recommendations",
        "/api/v1/library",
        "/api/v1/library/{entry_id}",
        "/api/v1/library/{entry_id}/cycles",
        "/api/v1/library/{entry_id}/events",
        "/api/v1/cycles/{cycle_id}",
        "/api/v1/cycles/{cycle_id}/events",
        "/api/v1/cycles/{cycle_id}/complete",
        "/api/v1/tv/episodes/{episode_id}/viewings",
        "/api/v1/activity",
        "/api/v1/arena/{media_type}/matchup",
        "/api/v1/arena/{media_type}/comparisons",
        "/api/v1/arena/{media_type}/rankings",
        "/api/v1/reports/year/{year}",
        "/api/v1/reports/summary",
        "/api/v1/recommendations/{media_type}",
    }
    assert expected_paths <= set(document["paths"])
