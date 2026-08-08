export type MediaType = "movie" | "tv" | "game" | "book";
export type LibraryStatus = "planned" | "in_progress" | "caught_up" | "completed" | "paused" | "dropped";

export type PublicRating = {
  source: string;
  value: number;
  scale?: number;
  count?: number | null;
  normalized_10: number;
};

export type MediaSummary = {
  media_id?: string | null;
  provider: string;
  external_id: string;
  media_type: MediaType;
  title: string;
  description?: string | null;
  release_date?: string | null;
  poster_url?: string | null;
  public_rating?: PublicRating | null;
  genres?: string[];
};

export type MediaDetail = MediaSummary & {
  original_title?: string | null;
  original_language?: string | null;
  backdrop_url?: string | null;
  credits?: Array<{ name: string; role: string; character?: string | null; order?: number | null }>;
  extra?: Record<string, unknown>;
};

export type LibraryEntry = {
  id: string;
  media_id: string;
  status: LibraryStatus;
  favorite: boolean;
  manual_rating?: number | null;
  notes?: string | null;
  media?: MediaSummary;
  updated_at: string;
};

export type Consumption = {
  id: string;
  library_entry_id: string;
  sequence_number: number;
  completed_on?: string | null;
  season_id?: string | null;
  rating?: number | null;
  notes?: string | null;
  created_at: string;
  updated_at: string;
};

export type SeasonSummary = {
  id: string;
  season_number: number;
  title?: string | null;
  air_date?: string | null;
  episode_count?: number | null;
  watched_count: number;
  latest_rating?: number | null;
  latest_completed_on?: string | null;
};

export type HistoryItem = Consumption & {
  media_id: string;
  media_type: MediaType;
  title: string;
  poster_url?: string | null;
  season_title?: string | null;
  season_number?: number | null;
};

export type ReportSummary = {
  library_items: number;
  completed_items: number;
  favorites: number;
  average_manual_rating?: number | null;
};

export type DailyActivity = { date: string; count: number };

export type YearReport = {
  year: number;
  total_events: number;
  active_days: number;
  completed_items: number;
  calendar: DailyActivity[];
};

export type ArenaMatchup = {
  media_type: MediaType;
  left_media_id: string;
  right_media_id: string;
  mode: "guided" | "random";
  left_media: MediaSummary;
  right_media: MediaSummary;
};

export type ArenaRanking = {
  media_id: string;
  elo: number;
  battle_score: number;
  rank: number;
  percentile: number;
  matches: number;
  provisional: boolean;
};

export type Page<T> = { items: T[]; next_cursor?: string | null };
