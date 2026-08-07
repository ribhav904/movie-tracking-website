from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.tracking import LibraryEntry
from app.repositories.catalog import CatalogRepository
from app.repositories.library import LibraryRepository
from app.schemas.tracking import LibraryCreate, LibraryUpdate


class LibraryService:
    def __init__(
        self, repository: LibraryRepository, catalog_repository: CatalogRepository
    ) -> None:
        self.repository = repository
        self.catalog_repository = catalog_repository

    async def create(self, payload: LibraryCreate) -> LibraryEntry:
        if await self.catalog_repository.get(payload.media_id) is None:
            raise NotFoundError("MEDIA_NOT_FOUND", "Import the media item before adding it.")
        if await self.repository.get_by_media(payload.media_id):
            raise ConflictError("LIBRARY_ENTRY_EXISTS", "This item is already in the library.")
        return await self.repository.create(payload)

    async def get(self, entry_id: UUID) -> LibraryEntry:
        entry = await self.repository.get(entry_id)
        if entry is None:
            raise NotFoundError("LIBRARY_ENTRY_NOT_FOUND", "The library entry does not exist.")
        return entry

    async def update(self, entry_id: UUID, payload: LibraryUpdate) -> LibraryEntry:
        return await self.repository.update(await self.get(entry_id), payload)

    async def delete(self, entry_id: UUID) -> None:
        await self.repository.delete(await self.get(entry_id))
