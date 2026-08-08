import httpx
import pytest
import respx

from app.db.models.enums import DiscoverMode, MediaType
from app.integrations.tmdb import TMDBClient


@pytest.mark.asyncio
@respx.mock
async def test_tmdb_search_normalizes_public_rating() -> None:
    respx.get("https://api.themoviedb.org/3/search/movie").mock(
        return_value=httpx.Response(
            200,
            json={
                "results": [
                    {
                        "id": 1,
                        "title": "Example",
                        "vote_average": 8.2,
                        "vote_count": 10,
                        "release_date": "2020-01-01",
                    }
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        result = await TMDBClient(client, "token").search("Example", MediaType.MOVIE)
    assert result[0].title == "Example"
    assert result[0].public_rating is not None
    assert result[0].public_rating.normalized_10 == 8.2


@pytest.mark.asyncio
@respx.mock
async def test_tmdb_discovery_mode_uses_the_matching_provider_endpoint() -> None:
    route = respx.get("https://api.themoviedb.org/3/movie/top_rated").mock(
        return_value=httpx.Response(200, json={"results": []})
    )
    async with httpx.AsyncClient() as client:
        result = await TMDBClient(client, "token").discover(
            MediaType.MOVIE, mode=DiscoverMode.TOP_RATED
        )

    assert route.called
    assert result == []
