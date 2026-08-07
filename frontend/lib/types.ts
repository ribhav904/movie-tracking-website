export type MediaType = "movie" | "tv" | "game" | "book";
export type LibraryStatus = "planned" | "in_progress" | "completed" | "paused" | "dropped";

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

export type Activity = {
  id: string;
  media_id: string;
  media?: MediaSummary;
  kind: "started" | "session" | "progress" | "episode_watched" | "completed" | "note" | "rated";
  occurred_at: string;
  occurred_on: string;
  duration_minutes?: number | null;
  progress_after?: number | null;
  notes?: string | null;
};

export type ActivityCreate = {
  kind: Activity["kind"];
  occurred_at: string;
  occurred_on: string;
  amount?: number | null;
  duration_minutes?: number | null;
  progress_after?: number | null;
  notes?: string | null;
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
