from uuid import UUID

from app.core.exceptions import ConflictError, NotFoundError
from app.db.models.arena import ArenaComparison, ArenaRating
from app.db.models.enums import ArenaOutcome, MediaType
from app.repositories.arena import ArenaRepository
from app.schemas.arena import ArenaMatchup, ArenaRanking


def expected_score(player_elo: float, opponent_elo: float) -> float:
    return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))


def updated_elo(current: float, opponent: float, actual: float, k_factor: int) -> float:
    return current + k_factor * (actual - expected_score(current, opponent))


def display_battle_score(elo: float, lowest_elo: float, highest_elo: float) -> float:
    """Map a title's Elo to its position in this user's current 0–10 arena range."""
    if highest_elo == lowest_elo:
        return 5.0
    score = round(10 * (elo - lowest_elo) / (highest_elo - lowest_elo), 1)
    return min(10.0, max(0.0, score))


class ArenaService:
    def __init__(self, repository: ArenaRepository) -> None:
        self.repository = repository

    async def matchup(self, media_type: MediaType, mode: str) -> ArenaMatchup:
        pair = await self.repository.select_matchup(media_type, mode)
        if pair is None:
            raise NotFoundError("NO_ARENA_MATCHUP", "No unplayed eligible matchup is available.")
        left_id, right_id = pair[0].media_id, pair[1].media_id
        summaries = await self.repository.media_summaries((left_id, right_id))
        if left_id not in summaries or right_id not in summaries:
            raise NotFoundError("ARENA_MEDIA_NOT_FOUND", "An Arena title could not be loaded.")
        return ArenaMatchup(
            media_type=media_type,
            left_media_id=left_id,
            right_media_id=right_id,
            mode=mode,
            left_media=summaries[left_id],
            right_media=summaries[right_id],
        )

    async def record(
        self,
        media_type: MediaType,
        left_id: UUID,
        right_id: UUID,
        outcome: ArenaOutcome,
        idempotency_key: str,
    ) -> ArenaComparison:
        if left_id == right_id:
            raise ConflictError("INVALID_ARENA_PAIR", "An item cannot battle itself.")
        existing = await self.repository.comparison_by_idempotency(idempotency_key)
        if existing:
            return existing
        if await self.repository.pair_exists(left_id, right_id):
            raise ConflictError("ARENA_PAIR_ALREADY_PLAYED", "This pair has already been decided.")
        await self.repository.ensure_eligible_ratings(media_type)
        ratings = await self.repository.lock_ratings(media_type, (left_id, right_id))
        if left_id not in ratings or right_id not in ratings:
            raise NotFoundError(
                "ARENA_ITEM_NOT_ELIGIBLE", "Both items must be completed and in this arena."
            )
        left, right = ratings[left_id], ratings[right_id]
        left_before, right_before = left.elo, right.elo
        left_k, right_k = _k(left), _k(right)
        left_actual, right_actual = {
            ArenaOutcome.LEFT: (1.0, 0.0),
            ArenaOutcome.RIGHT: (0.0, 1.0),
            ArenaOutcome.TIE: (0.5, 0.5),
        }[outcome]
        left.elo = updated_elo(left_before, right_before, left_actual, left_k)
        right.elo = updated_elo(right_before, left_before, right_actual, right_k)
        left.matches += 1
        right.matches += 1
        _increment_record(left, right, outcome)
        return await self.repository.add_comparison(
            media_type=media_type,
            left=left,
            right=right,
            outcome=outcome,
            left_before=left_before,
            right_before=right_before,
            left_k=left_k,
            right_k=right_k,
            idempotency_key=idempotency_key,
        )

    async def rankings(self, media_type: MediaType) -> list[ArenaRanking]:
        # Expose every eligible completed title in the library immediately,
        # including its provisional 1500 Elo, rather than only after the user
        # opens a first matchup.
        await self.repository.ensure_eligible_ratings(media_type)
        rows = await self.repository.rankings(media_type)
        total = len(rows)
        lowest_elo = min((row.elo for row in rows), default=1500.0)
        highest_elo = max((row.elo for row in rows), default=1500.0)
        return [
            ArenaRanking(
                media_id=row.media_id,
                elo=round(row.elo, 2),
                battle_score=display_battle_score(row.elo, lowest_elo, highest_elo),
                rank=index + 1,
                percentile=round(100 * (total - index - 1) / max(total - 1, 1), 1),
                matches=row.matches,
                provisional=row.matches < 5,
            )
            for index, row in enumerate(rows)
        ]


def _k(rating: ArenaRating) -> int:
    return 40 if rating.matches < 10 else 20


def _increment_record(left: ArenaRating, right: ArenaRating, outcome: ArenaOutcome) -> None:
    if outcome == ArenaOutcome.LEFT:
        left.wins += 1
        right.losses += 1
    elif outcome == ArenaOutcome.RIGHT:
        left.losses += 1
        right.wins += 1
    else:
        left.ties += 1
        right.ties += 1
