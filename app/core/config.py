from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    APP_ENV: Literal["local", "test", "production"] = "local"
    APP_NAME: str = "Entertainment Tracker API"
    API_PREFIX: str = "/api/v1"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"
    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    DATABASE_URL: str
    SUPABASE_URL: AnyHttpUrl
    SUPABASE_PUBLISHABLE_KEY: str
    SUPABASE_SECRET_KEY: str
    SUPABASE_JWT_AUDIENCE: str = "authenticated"

    TMDB_ACCESS_TOKEN: str = ""
    IGDB_CLIENT_ID: str = ""
    IGDB_CLIENT_SECRET: str = ""
    GOOGLE_BOOKS_API_KEY: str = ""
    OPEN_LIBRARY_CONTACT: str = ""

    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 5
    PROVIDER_TIMEOUT_SECONDS: float = 10.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def supabase_jwks_url(self) -> str:
        return f"{str(self.SUPABASE_URL).rstrip('/')}/auth/v1/.well-known/jwks.json"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def supabase_issuer(self) -> str:
        return f"{str(self.SUPABASE_URL).rstrip('/')}/auth/v1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
