import httpx
import pytest
import respx

from app.db.models.enums import MediaType
from app.integrations.google_books import GoogleBooksClient
from app.integrations.igdb import IGDBClient
from app.integrations.open_library import OpenLibraryClient


@pytest.mark.asyncio
@respx.mock
async def test_google_books_normalizes_rating_and_limits_page_size() -> None:
    route = respx.get("https://www.googleapis.com/books/v1/volumes").mock(
        return_value=httpx.Response(
            200,
            json={
                "items": [
                    {
                        "id": "volume-1",
                        "volumeInfo": {
                            "title": "A Book",
                            "averageRating": 4.5,
                            "ratingsCount": 12,
                        },
                    }
                ]
            },
        )
    )
    async with httpx.AsyncClient() as client:
        items = await GoogleBooksClient(client, "key").search(
            "science fiction", MediaType.BOOK, page=2
        )

    assert route.called
    assert route.calls[0].request.url.params["maxResults"] == "20"
    assert route.calls[0].request.url.params["startIndex"] == "20"
    assert items[0].public_rating is not None
    assert items[0].public_rating.normalized_10 == 9


@pytest.mark.asyncio
@respx.mock
async def test_open_library_identifies_the_application() -> None:
    route = respx.get("https://openlibrary.org/search.json").mock(
        return_value=httpx.Response(
            200,
            json={"docs": [{"key": "/works/OL1W", "title": "Open Book"}]},
        )
    )
    async with httpx.AsyncClient() as client:
        items = await OpenLibraryClient(client, "owner@example.com").search("open", MediaType.BOOK)

    assert route.calls[0].request.headers["user-agent"] == (
        "EntertainmentTracker (owner@example.com)"
    )
    assert items[0].external_id == "OL1W"


@pytest.mark.asyncio
@respx.mock
async def test_igdb_uses_app_token_and_normalizes_100_point_rating() -> None:
    respx.post("https://id.twitch.tv/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "token", "expires_in": 3600})
    )
    route = respx.post("https://api.igdb.com/v4/games").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 10,
                    "name": "A Game",
                    "total_rating": 84,
                    "total_rating_count": 100,
                }
            ],
        )
    )
    async with httpx.AsyncClient() as client:
        items = await IGDBClient(client, "client-id", "client-secret").search(
            "game", MediaType.GAME
        )

    assert route.calls[0].request.headers["client-id"] == "client-id"
    assert route.calls[0].request.headers["authorization"] == "Bearer token"
    assert items[0].public_rating is not None
    assert items[0].public_rating.normalized_10 == 8.4
