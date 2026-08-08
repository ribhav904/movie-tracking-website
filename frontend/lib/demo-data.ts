import type { LibraryEntry, MediaDetail, MediaSummary, Page, ReportSummary, YearReport } from "@/lib/types";

// Preview mode deliberately starts empty. It exists only so the local interface
// can render before credentials are configured; it never represents real data.
const emptyLibrary: Page<LibraryEntry> = { items: [] };
const emptyMedia: Page<MediaSummary> = { items: [] };
const emptySummary: ReportSummary = { library_items: 0, completed_items: 0, favorites: 0, average_manual_rating: null };
const emptyReport: YearReport = { year: 2026, total_events: 0, active_days: 0, completed_items: 0, calendar: [] };

export function getDemoResponse(path: string): unknown {
  if (path.startsWith("/reports/summary")) return emptySummary;
  if (path.startsWith("/reports/year/")) return emptyReport;
  if (path.startsWith("/library") || path.startsWith("/history")) return emptyLibrary;
  if (path.startsWith("/media/search") || path.startsWith("/media/discover") || path.startsWith("/recommendations")) return emptyMedia;
  if (path.startsWith("/media/")) return null as MediaDetail | null;
  return {};
}
