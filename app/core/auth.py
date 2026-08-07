import asyncio
import time
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import httpx
import jwt
from jwt import PyJWK

from app.core.config import Settings
from app.core.exceptions import AppError
from app.db.models.enums import MembershipRole


@dataclass(frozen=True, slots=True)
class CurrentUser:
    id: UUID
    role: MembershipRole
    email: str | None


class SupabaseJWTVerifier:
    def __init__(self, settings: Settings, client: httpx.AsyncClient) -> None:
        self._settings = settings
        self._client = client
        self._keys: dict[str, PyJWK] = {}
        self._expires_at = 0.0
        self._lock = asyncio.Lock()

    async def _refresh_keys(self) -> None:
        async with self._lock:
            if self._keys and time.monotonic() < self._expires_at:
                return
            response = await self._client.get(self._settings.supabase_jwks_url)
            response.raise_for_status()
            payload = response.json()
            self._keys = {
                str(item["kid"]): PyJWK.from_dict(item) for item in payload.get("keys", [])
            }
            self._expires_at = time.monotonic() + 600

    async def verify(self, token: str) -> dict[str, Any]:
        try:
            header = jwt.get_unverified_header(token)
            kid = str(header["kid"])
            if kid not in self._keys or time.monotonic() >= self._expires_at:
                self._expires_at = 0
                await self._refresh_keys()
            key = self._keys.get(kid)
            if key is None:
                self._expires_at = 0
                await self._refresh_keys()
                key = self._keys.get(kid)
            if key is None:
                raise jwt.InvalidKeyError("Unknown signing key")
            return jwt.decode(
                token,
                key=key.key,
                algorithms=["ES256", "RS256"],
                audience=self._settings.SUPABASE_JWT_AUDIENCE,
                issuer=self._settings.supabase_issuer,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
        except (jwt.PyJWTError, httpx.HTTPError, KeyError, ValueError) as exc:
            raise AppError(
                "INVALID_ACCESS_TOKEN",
                "The access token is invalid or expired.",
                status_code=401,
            ) from exc
