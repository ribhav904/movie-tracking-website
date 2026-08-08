import random
from typing import cast
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.arena import ArenaComparison, ArenaRating
from app.db.models.catalog import MediaItem, MediaSource
from app.db.models.enums import ArenaOutcome, MediaType
from app.db.models.tracking import ConsumptionRecord, LibraryEntry
from app.schemas.media import MediaSummary, PublicRating


class ArenaRepository:
    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def ensure_eligible_ratings(self, media_type: MediaType) -> list[ArenaRating]:
        eligible = list(
            await self.session.scalars(
                select(MediaItem.id)
                .join(LibraryEntry, LibraryEntry.media_id == MediaItem.id)
                .join(ConsumptionRecord, ConsumptionRecord.library_entry_id == LibraryEntry.id)
                .where(
                    LibraryEntry.user_id == self.user_id,
                    MediaItem.media_type == media_type,
                    ConsumptionRecord.user_id == self.user_id,
                )
                .distinct()
            )
        )
        existing = list(
            await self.session.scalars(
                select(ArenaRating).where(
                    ArenaRating.user_id == self.user_id, ArenaRating.media_type == media_type
                )
            )
        )
        existing_ids = {rating.media_id for rating in existing}
        new_rows = [
            ArenaRating(user_id=self.user_id, media_id=media_id, media_type=media_type)
            for media_id in eligible
            if media_id not in existing_ids
        ]
        self.session.add_all(new_rows)
        if new_rows:
            await self.session.flush()
        return [*existing, *new_rows]

    async def compared_pairs(self, media_type: MediaType) -> set[tuple[UUID, UUID]]:
        rows = await self.session.execute(
            select(ArenaComparison.media_low_id, ArenaComparison.media_high_id).where(
                ArenaComparison.user_id == self.user_id,
                ArenaComparison.media_type == media_type,
            )
        )
        return {(row[0], row[1]) for row in rows}

    async def select_matchup(
        self, media_type: MediaType, mode: str
    ) -> tuple[ArenaRating, ArenaRating] | None:
        ratings = await self.ensure_eligible_ratings(media_type)
        if len(ratings) < 2:
            return None
        compared = await self.compared_pairs(media_type)
        pairs = [
            (left, right)
            for index, left in enumerate(ratings)
            for right in ratings[index + 1 :]
            if _pair(left.media_id, right.media_id) not in compared
        ]
        if not pairs:
            return None
        if mode == "random":
            weights = [1 / (1 + left.matches + right.matches) for left, right in pairs]
            return random.choices(pairs, weights=weights, k=1)[0]
        provisional = [pair for pair in pairs if pair[0].matches < 5 or pair[1].matches < 5]
        candidates = provisional or pairs
        return min(
            candidates,
            key=lambda pair: (
                min(pair[0].matches, pair[1].matches),
                abs(pair[0].elo - pair[1].elo),
            ),
        )

    async def lock_ratings(
        self, media_type: MediaType, media_ids: tuple[UUID, UUID]
    ) -> dict[UUID, ArenaRating]:
        rows = await self.session.scalars(
            select(ArenaRating)
            .where(
                ArenaRating.user_id == self.user_id,
                ArenaRating.media_type == media_type,
                ArenaRating.media_id.in_(media_ids),
            )
            .order_by(ArenaRating.media_id)
            .with_for_update()
        )
        return {row.media_id: row for row in rows}

    async def comparison_by_idempotency(self, key: str) -> ArenaComparison | None:
        return cast(
            ArenaComparison | None,
            await self.session.scalar(
                select(ArenaComparison).where(
                    ArenaComparison.user_id == self.user_id,
                    ArenaComparison.idempotency_key == key,
                )
            ),
        )

    async def pair_exists(self, left_id: UUID, right_id: UUID) -> bool:
        low, high = _pair(left_id, right_id)
        return (
            await self.session.scalar(
                select(ArenaComparison.id).where(
                    ArenaComparison.user_id == self.user_id,
                    ArenaComparison.media_low_id == low,
                    ArenaComparison.media_high_id == high,
                )
            )
            is not None
        )

    async def add_comparison(
        self,
        *,
        media_type: MediaType,
        left: ArenaRating,
        right: ArenaRating,
        outcome: ArenaOutcome,
        left_before: float,
        right_before: float,
        left_k: int,
        right_k: int,
        idempotency_key: str,
    ) -> ArenaComparison:
        low, high = _pair(left.media_id, right.media_id)
        row = ArenaComparison(
            user_id=self.user_id,
            media_type=media_type,
            media_low_id=low,
            media_high_id=high,
            left_media_id=left.media_id,
            right_media_id=right.media_id,
            outcome=outcome,
            left_elo_before=left_before,
            right_elo_before=right_before,
            left_elo_after=left.elo,
            right_elo_after=right.elo,
            left_k_factor=left_k,
            right_k_factor=right_k,
            idempotency_key=idempotency_key,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def rankings(self, media_type: MediaType) -> list[ArenaRating]:
        return list(
            await self.session.scalars(
                select(ArenaRating)
                .where(
                    ArenaRating.user_id == self.user_id,
                    ArenaRating.media_type == media_type,
                )
                .order_by(ArenaRating.elo.desc(), ArenaRating.media_id)
            )
        )

    async def media_summaries(self, media_ids: tuple[UUID, UUID]) -> dict[UUID, MediaSummary]:
        rows = await self.session.execute(
            select(MediaItem, MediaSource)
            .join(MediaSource, MediaSource.media_id == MediaItem.id)
            .where(MediaItem.id.in_(media_ids))
        )
        summaries: dict[UUID, MediaSummary] = {}
        for item, source in rows:
            public_rating = (
                PublicRating(
                    source=item.public_rating_source,
                    value=float(source.raw_rating),
                    scale=float(source.raw_rating_scale),
                    count=source.raw_rating_count,
                    normalized_10=float(item.public_rating),
                )
                if (
                    item.public_rating is not None
                    and item.public_rating_source is not None
                    and source.raw_rating is not None
                    and source.raw_rating_scale is not None
                )
                else None
            )
            summaries[item.id] = MediaSummary(
                media_id=item.id,
                provider=source.provider,
                external_id=source.external_id,
                media_type=item.media_type,
                title=item.title,
                description=item.description,
                release_date=item.release_date,
                poster_url=item.poster_url,
                public_rating=public_rating,
            )
        return summaries


def _pair(left_id: UUID, right_id: UUID) -> tuple[UUID, UUID]:
    return (left_id, right_id) if left_id.int < right_id.int else (right_id, left_id)
