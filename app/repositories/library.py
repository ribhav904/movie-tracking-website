from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.tracking import LibraryEntry
from app.schemas.tracking import LibraryCreate, LibraryUpdate


class LibraryRepository:
    def __init__(self, session: AsyncSession, user_id: UUID) -> None:
        self.session = session
        self.user_id = user_id

    async def list(self, *, offset: int = 0, limit: int = 50) -> list[LibraryEntry]:
        rows = await self.session.scalars(
            select(LibraryEntry)
            .where(LibraryEntry.user_id == self.user_id)
            .order_by(LibraryEntry.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(rows)

    async def get(self, entry_id: UUID) -> LibraryEntry | None:
        return cast(
            LibraryEntry | None,
            await self.session.scalar(
                select(LibraryEntry).where(
                    LibraryEntry.id == entry_id,
                    LibraryEntry.user_id == self.user_id,
                )
            ),
        )

    async def get_by_media(self, media_id: UUID) -> LibraryEntry | None:
        return cast(
            LibraryEntry | None,
            await self.session.scalar(
                select(LibraryEntry).where(
                    LibraryEntry.media_id == media_id,
                    LibraryEntry.user_id == self.user_id,
                )
            ),
        )

    async def create(self, payload: LibraryCreate) -> LibraryEntry:
        entry = LibraryEntry(user_id=self.user_id, **payload.model_dump())
        self.session.add(entry)
        await self.session.flush()
        return entry

    async def update(self, entry: LibraryEntry, payload: LibraryUpdate) -> LibraryEntry:
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(entry, key, value)
        await self.session.flush()
        return entry

    async def delete(self, entry: LibraryEntry) -> None:
        await self.session.delete(entry)

    async def stats(self) -> tuple[int, int, int, float | None]:
        result = await self.session.execute(
            select(
                func.count(LibraryEntry.id),
                func.count(LibraryEntry.id).filter(LibraryEntry.status == "completed"),
                func.count(LibraryEntry.id).filter(LibraryEntry.favorite.is_(True)),
                func.avg(LibraryEntry.manual_rating),
            ).where(LibraryEntry.user_id == self.user_id)
        )
        total, completed, favorites, average = result.one()
        return int(total), int(completed), int(favorites), float(average) if average else None
