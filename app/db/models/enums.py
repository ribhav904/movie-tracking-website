from enum import StrEnum


class MembershipRole(StrEnum):
    OWNER = "owner"
    MEMBER = "member"


class MediaType(StrEnum):
    MOVIE = "movie"
    TV = "tv"
    GAME = "game"
    BOOK = "book"


class MediaProvider(StrEnum):
    TMDB = "tmdb"
    IGDB = "igdb"
    GOOGLE_BOOKS = "google_books"
    OPEN_LIBRARY = "open_library"


class LibraryStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    DROPPED = "dropped"


class CycleState(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class ActivityKind(StrEnum):
    STARTED = "started"
    PROGRESS = "progress"
    SESSION = "session"
    EPISODE_WATCHED = "episode_watched"
    COMPLETED = "completed"
    RATED = "rated"
    NOTE = "note"


class ArenaOutcome(StrEnum):
    LEFT = "left"
    RIGHT = "right"
    TIE = "tie"


def enum_values(enum_class: type[StrEnum]) -> list[str]:
    return [item.value for item in enum_class]
