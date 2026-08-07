from app.db.models.enums import MediaProvider, MediaType
from app.integrations.base import MediaProviderClient


class ProviderRegistry:
    def __init__(self, providers: dict[MediaProvider, MediaProviderClient]) -> None:
        self._providers = providers

    def get(self, provider: MediaProvider) -> MediaProviderClient:
        return self._providers[provider]

    def primary_for(self, media_type: MediaType) -> MediaProviderClient:
        provider = {
            MediaType.MOVIE: MediaProvider.TMDB,
            MediaType.TV: MediaProvider.TMDB,
            MediaType.GAME: MediaProvider.IGDB,
            MediaType.BOOK: MediaProvider.GOOGLE_BOOKS,
        }[media_type]
        return self.get(provider)
