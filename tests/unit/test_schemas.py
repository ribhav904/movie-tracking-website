import pytest
from pydantic import ValidationError

from app.schemas.tracking import LibraryCreate


def test_manual_rating_accepts_half_steps() -> None:
    payload = LibraryCreate(media_id="a2214ccf-09bd-45db-8365-4bc5c438b3fd", manual_rating=8.5)
    assert payload.manual_rating == 8.5


def test_manual_rating_rejects_other_increments() -> None:
    with pytest.raises(ValidationError):
        LibraryCreate(media_id="a2214ccf-09bd-45db-8365-4bc5c438b3fd", manual_rating=8.3)
