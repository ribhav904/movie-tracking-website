import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from sqlalchemy import select

from app.core.exceptions import AppError, NotFoundError
from app.db.models.catalog import MediaSource
from app.db.models.enums import DiscoverMode, MediaProvider, MediaType
from app.integrations import ProviderRegistry
from app.repositories.catalog import CatalogRepository
from app.schemas.media import MediaDetail, MediaSummary


class MediaService:
    def __init__(self, registry: ProviderRegistry, repository: CatalogRepository) -> None:
        self.registry = registry
        self.repository = repository

    async def search(self, query: str, media_type: MediaType, page: int) -> list[MediaSummary]:
        provider = self.registry.primary_for(media_type)
        try:
            results = await provider.search(query, media_type, page=page)
            if not results and media_type == MediaType.BOOK:
                results = await self.registry.get(MediaProvider.OPEN_LIBRARY).search(
                    query, media_type, page=page
                )
            return results
        except httpx.HTTPError as exc:
            if media_type == MediaType.BOOK:
                try:
                    return await self.registry.get(MediaProvider.OPEN_LIBRARY).search(
                        query, media_type, page=page
                    )
                except httpx.HTTPError:
                    pass
            raise AppError(
                "PROVIDER_UNAVAILABLE",
                "The media provider is temporarily unavailable.",
                status_code=503,
            ) from exc

    async def search_all(self, query: str, page: int) -> list[MediaSummary]:
        results = await asyncio.gather(
            *(self.search(query, media_type, page) for media_type in MediaType),
            return_exceptions=True,
        )
        items: list[MediaSummary] = []
        for result in results:
            if not isinstance(result, list):
                continue
            # A balanced list makes a universal search useful without one
            # provider crowding out the other media types.
            items.extend(result[:10])
        if not items:
            raise AppError(
                "PROVIDER_UNAVAILABLE",
                "Media providers are temporarily unavailable.",
                status_code=503,
            )
        return items

    async def detail(
        self, provider: MediaProvider, media_type: MediaType, external_id: str
    ) -> MediaDetail:
        existing = await self.repository.get_by_source(provider, media_type, external_id)
        if existing:
            item, source = existing
            if source.fetched_at >= datetime.now(UTC) - timedelta(days=7):
                payload = dict(source.normalized_payload)
                payload["media_id"] = item.id
                return MediaDetail.model_validate(payload)
        try:
            detail = await self.registry.get(provider).detail(external_id, media_type)
            item = await self.repository.upsert(detail)
            return detail.model_copy(update={"media_id": item.id})
        except httpx.HTTPError as exc:
            if existing:
                payload = dict(existing[1].normalized_payload)
                payload["media_id"] = existing[0].id
                return MediaDetail.model_validate(payload)
            raise AppError(
                "PROVIDER_UNAVAILABLE",
                "The media provider is temporarily unavailable.",
                status_code=503,
            ) from exc

    async def by_id(self, media_id: UUID) -> MediaSummary:
        item = await self.repository.get(media_id)
        if item is None:
            raise NotFoundError("MEDIA_NOT_FOUND", "The requested media item does not exist.")
        source = await self.repository.session.scalar(
            select(MediaSource).where(MediaSource.media_id == media_id)
        )
        if source is None:
            raise NotFoundError("MEDIA_SOURCE_NOT_FOUND", "The media source does not exist.")
        return MediaSummary(
            media_id=item.id,
            provider=source.provider,
            external_id=source.external_id,
            media_type=item.media_type,
            title=item.title,
            description=item.description,
            release_date=item.release_date,
            poster_url=item.poster_url,
            public_rating=(
                {
                    "source": item.public_rating_source,
                    "value": float(source.raw_rating),
                    "scale": float(source.raw_rating_scale),
                    "count": source.raw_rating_count,
                    "normalized_10": float(item.public_rating),
                }
                if (
                    item.public_rating is not None
                    and source.raw_rating is not None
                    and source.raw_rating_scale is not None
                )
                else None
            ),
        )

    async def detail_by_id(self, media_id: UUID) -> MediaDetail:
        item = await self.repository.get(media_id)
        source = await self.repository.source_for_media(media_id)
        if item is None or source is None:
            raise NotFoundError("MEDIA_NOT_FOUND", "The media item does not exist.")
        payload = dict(source.normalized_payload)
        payload["media_id"] = item.id
        return MediaDetail.model_validate(payload)

    async def discover(
        self, media_type: MediaType, page: int, mode: DiscoverMode
    ) -> list[MediaSummary]:
        provider = self.registry.primary_for(media_type)
        try:
            return await provider.discover(media_type, page=page, mode=mode)
        except httpx.HTTPError as exc:
            if media_type == MediaType.BOOK:
                try:
                    return await self.registry.get(MediaProvider.OPEN_LIBRARY).search(
                        "popular fiction", media_type, page=page
                    )
                except httpx.HTTPError:
                    pass
            raise AppError(
                "PROVIDER_UNAVAILABLE",
                "The media provider is temporarily unavailable.",
                status_code=503,
            ) from exc
