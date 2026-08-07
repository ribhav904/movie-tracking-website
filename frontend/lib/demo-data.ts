import type {
  Activity,
  LibraryEntry,
  MediaSummary,
  Page,
  ReportSummary,
  YearReport,
} from "@/lib/types";

export const demoMedia: MediaSummary[] = [
  {
    media_id: "m-1",
    provider: "tmdb",
    external_id: "496243",
    media_type: "movie",
    title: "Parasite",
    description: "A sharp, unsettling family thriller with an immaculate sense of structure.",
    release_date: "2019-05-30",
    public_rating: { source: "TMDB", value: 8.5, count: 19200, normalized_10: 8.5 },
    genres: ["Thriller", "Drama"],
  },
  {
    media_id: "m-2",
    provider: "tmdb",
    external_id: "1396",
    media_type: "tv",
    title: "Breaking Bad",
    description: "A chemistry teacher turns precision into an art form.",
    release_date: "2008-01-20",
    public_rating: { source: "TMDB", value: 8.9, count: 16000, normalized_10: 8.9 },
    genres: ["Crime", "Drama"],
  },
  {
    media_id: "m-3",
    provider: "igdb",
    external_id: "7346",
    media_type: "game",
    title: "Hades",
    description: "A restless escape through an underworld that remembers every attempt.",
    release_date: "2020-09-17",
    public_rating: { source: "IGDB", value: 93, scale: 100, count: 4000, normalized_10: 9.3 },
    genres: ["Roguelike", "Action"],
  },
  {
    media_id: "m-4",
    provider: "google_books",
    external_id: "book-1",
    media_type: "book",
    title: "The Left Hand of Darkness",
    description: "A patient, exacting novel of climate, trust, and political distance.",
    release_date: "1969-03-01",
    public_rating: { source: "Google Books", value: 4.2, scale: 5, count: 7000, normalized_10: 8.4 },
    genres: ["Science fiction", "Classics"],
  },
  {
    media_id: "m-5",
    provider: "tmdb",
    external_id: "11324",
    media_type: "movie",
    title: "Shutter Island",
    description: "A closed-room mystery with the sea pressed against every wall.",
    release_date: "2010-02-14",
    public_rating: { source: "TMDB", value: 8.2, count: 24000, normalized_10: 8.2 },
    genres: ["Mystery", "Thriller"],
  },
  {
    media_id: "m-6",
    provider: "open_library",
    external_id: "OL1W",
    media_type: "book",
    title: "Piranesi",
    description: "An unforgettable house, an impossible tide, and one carefully kept journal.",
    release_date: "2020-09-15",
    public_rating: { source: "Open Library", value: 4.3, scale: 5, count: 5000, normalized_10: 8.6 },
    genres: ["Fantasy", "Mystery"],
  },
];

export const demoLibrary: LibraryEntry[] = [
  { id: "l-1", media_id: "m-1", status: "completed", favorite: true, manual_rating: 9.5, updated_at: "2026-08-06", media: demoMedia[0] },
  { id: "l-2", media_id: "m-2", status: "in_progress", favorite: true, manual_rating: null, updated_at: "2026-08-07", media: demoMedia[1] },
  { id: "l-3", media_id: "m-3", status: "in_progress", favorite: false, manual_rating: 9, updated_at: "2026-08-04", media: demoMedia[2] },
  { id: "l-4", media_id: "m-4", status: "completed", favorite: true, manual_rating: 8.5, updated_at: "2026-07-30", media: demoMedia[3] },
  { id: "l-5", media_id: "m-5", status: "planned", favorite: false, manual_rating: null, updated_at: "2026-07-23", media: demoMedia[4] },
  { id: "l-6", media_id: "m-6", status: "planned", favorite: false, manual_rating: null, updated_at: "2026-07-20", media: demoMedia[5] },
];

export const demoActivity: Activity[] = [
  { id: "a-1", media_id: "m-2", media: demoMedia[1], kind: "episode_watched", occurred_at: "2026-08-07T16:30:00+05:30", occurred_on: "2026-08-07", duration_minutes: 47, notes: "Season 3, episode 4" },
  { id: "a-2", media_id: "m-3", media: demoMedia[2], kind: "session", occurred_at: "2026-08-06T21:15:00+05:30", occurred_on: "2026-08-06", duration_minutes: 75, progress_after: 42 },
  { id: "a-3", media_id: "m-1", media: demoMedia[0], kind: "completed", occurred_at: "2026-08-05T22:05:00+05:30", occurred_on: "2026-08-05", notes: "The final turn still lands." },
  { id: "a-4", media_id: "m-4", media: demoMedia[3], kind: "rating", occurred_at: "2026-08-02T11:15:00+05:30", occurred_on: "2026-08-02", notes: "8.5 / 10" },
];

export const demoSummary: ReportSummary = {
  library_items: 126,
  completed_items: 74,
  favorites: 18,
  average_manual_rating: 8.2,
};

const activityCounts: Record<string, number> = {
  "2026-01-02": 1,
  "2026-01-11": 2,
  "2026-02-06": 1,
  "2026-02-14": 3,
  "2026-03-08": 1,
  "2026-03-23": 2,
  "2026-04-17": 1,
  "2026-05-03": 2,
  "2026-05-18": 4,
  "2026-06-05": 1,
  "2026-06-21": 2,
  "2026-07-12": 3,
  "2026-07-26": 1,
  "2026-08-02": 1,
  "2026-08-04": 1,
  "2026-08-05": 2,
  "2026-08-06": 1,
  "2026-08-07": 1,
};

export const demoYearReport: YearReport = {
  year: 2026,
  total_events: 156,
  active_days: Object.keys(activityCounts).length,
  completed_items: 11,
  calendar: Object.entries(activityCounts).map(([date, count]) => ({ date, count })),
};

export function getDemoResponse(path: string): unknown {
  if (path.startsWith("/reports/summary")) return demoSummary;
  if (path.startsWith("/reports/year/")) return demoYearReport;
  if (path.startsWith("/library")) return { items: demoLibrary } satisfies Page<LibraryEntry>;
  if (path.startsWith("/activity")) return { items: demoActivity } satisfies Page<Activity>;
  if (path.startsWith("/media/search") || path.startsWith("/media/discover")) {
    return { items: demoMedia } satisfies Page<MediaSummary>;
  }
  if (path.startsWith("/media/")) {
    const mediaId = path.split("/")[2];
    return demoMedia.find((item) => item.media_id === mediaId) ?? demoMedia[0];
  }
  if (path.startsWith("/recommendations")) return { items: [demoMedia[4], demoMedia[5]] } satisfies Page<MediaSummary>;
  return {};
}
