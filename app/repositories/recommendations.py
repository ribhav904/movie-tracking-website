from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.catalog import MediaGenre, MediaItem
from app.db.models.enums import MediaType
from app.db.models.tracking import LibraryEntry


class RecommendationRepository:
    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def candidates(self, media_type: MediaType, limit: int = 20) -> list[MediaItem]:
        liked_media = (
            select(LibraryEntry.media_id)
            .where(
                LibraryEntry.user_id == self.user_id,
                (LibraryEntry.favorite.is_(True)) | (LibraryEntry.manual_rating >= 7),
            )
            .subquery()
        )
        liked_genres = (
            select(MediaGenre.name)
            .where(MediaGenre.media_id.in_(select(liked_media.c.media_id)))
            .subquery()
        )
        tracked = select(LibraryEntry.media_id).where(LibraryEntry.user_id == self.user_id)
        score = func.count(MediaGenre.id).label("genre_score")
        rows = await self.session.execute(
            select(MediaItem)
            .join(MediaGenre, MediaGenre.media_id == MediaItem.id)
            .where(
                MediaItem.media_type == media_type,
                MediaGenre.name.in_(select(liked_genres.c.name)),
                MediaItem.id.not_in(tracked),
            )
            .group_by(MediaItem.id)
            .order_by(score.desc(), MediaItem.public_rating.desc().nullslast())
            .limit(limit)
        )
        return list(rows.scalars())
