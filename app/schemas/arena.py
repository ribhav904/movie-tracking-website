from datetime import datetime
from uuid import UUID

from app.db.models.enums import ArenaOutcome, MediaType
from app.schemas.common import APIModel
from app.schemas.media import MediaSummary


class ArenaMatchup(APIModel):
    media_type: MediaType
    left_media_id: UUID
    right_media_id: UUID
    mode: str
    left_media: MediaSummary
    right_media: MediaSummary


class ArenaComparisonCreate(APIModel):
    left_media_id: UUID
    right_media_id: UUID
    outcome: ArenaOutcome


class ArenaComparisonRead(APIModel):
    id: UUID
    outcome: ArenaOutcome
    left_media_id: UUID
    right_media_id: UUID
    left_elo_after: float
    right_elo_after: float
    created_at: datetime


class ArenaRanking(APIModel):
    media_id: UUID
    elo: float
    battle_score: float
    rank: int
    percentile: float
    matches: int
    provisional: bool
