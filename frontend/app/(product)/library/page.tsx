"use client";

import { useQueries, useQuery } from "@tanstack/react-query";
import { Heart, LayoutGrid, Rows3, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { MediaCard } from "@/components/media-card";
import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { ArenaRanking, LibraryEntry, LibraryStatus, MediaType, Page } from "@/lib/types";
import { useMediaMap } from "@/lib/use-media-map";

const statuses: Array<{ value: "all" | LibraryStatus; label: string }> = [
  { value: "all", label: "Everything" }, { value: "in_progress", label: "In progress" }, { value: "caught_up", label: "Caught up" }, { value: "planned", label: "Planned" }, { value: "completed", label: "Completed" }, { value: "paused", label: "Paused" },
];
const mediaTypes: MediaType[] = ["movie", "tv", "game", "book"];
const sortOptions = [
  { value: "updated", label: "Recently updated" },
  { value: "manual_desc", label: "My rating: high to low" },
  { value: "manual_asc", label: "My rating: low to high" },
  { value: "arena_desc", label: "Arena Score: high to low" },
  { value: "arena_asc", label: "Arena Score: low to high" },
] as const;
type SortOption = (typeof sortOptions)[number]["value"];
type LibraryItem = LibraryEntry & { arena?: ArenaRanking };

export default function LibraryPage() {
  const [status, setStatus] = useState<"all" | LibraryStatus>("all");
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");
  const [sort, setSort] = useState<SortOption>("updated");
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiRequest<Page<LibraryEntry>>("/library?limit=100") });
  const rankings = useQueries({ queries: mediaTypes.map((mediaType) => ({ queryKey: ["arena", mediaType, "rankings"], queryFn: () => apiRequest<ArenaRanking[]>(`/arena/${mediaType}/rankings`) })) });
  const mediaMap = useMediaMap(library.data?.items.map((entry) => entry.media_id) ?? []);
  const arenaByMedia = useMemo(() => new Map(rankings.flatMap((query) => query.data ?? []).map((ranking) => [ranking.media_id, ranking])), [rankings]);
  const entries = useMemo(() => {
    const filtered = (library.data?.items ?? [])
      .map((entry) => ({ ...entry, media: entry.media ?? mediaMap.get(entry.media_id), arena: arenaByMedia.get(entry.media_id) }))
      .filter((entry) => (status === "all" || entry.status === status) && (!search || entry.media?.title.toLowerCase().includes(search.toLowerCase())));
    return filtered.sort((left, right) => compareEntries(left, right, sort));
  }, [arenaByMedia, library.data, mediaMap, search, sort, status]);

  return <div className="page-stack">
    <PageHeader eyebrow="Your archive" title="A library that remembers context." description="Status, personal notes, and your personal and Arena ratings live alongside every title." />
    <section className="library-toolbar">
      <div className="status-tabs">{statuses.map((item) => <button key={item.value} className={status === item.value ? "is-active" : ""} onClick={() => setStatus(item.value)}>{item.label}</button>)}</div>
      <div className="toolbar-actions"><label className="search-field search-field--small"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter your library" /></label><label className="sort-select"><span>Sort</span><select value={sort} onChange={(event) => setSort(event.target.value as SortOption)}>{sortOptions.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</select></label><div className="view-switch"><button className={view === "grid" ? "is-active" : ""} aria-label="Grid view" onClick={() => setView("grid")}><LayoutGrid size={16} /></button><button className={view === "list" ? "is-active" : ""} aria-label="List view" onClick={() => setView("list")}><Rows3 size={16} /></button></div></div>
    </section>
    {view === "grid" ? <section className="media-grid">{entries.map((entry) => entry.media && <div className="library-card" key={entry.id}><MediaCard media={entry.media} /><RatingMeta entry={entry} />{entry.favorite && <Heart size={14} fill="currentColor" aria-label="Favourite" />}</div>)}</section> : <section className="library-list"><div className="library-list__heading"><span>Title</span><span>Status</span><span>My rating</span><span>Arena Score</span></div>{entries.map((entry) => <article key={entry.id} className="library-list__row"><span className={`type-dot type-dot--${entry.media?.media_type}`} /><div><h3>{entry.media?.title}</h3><p>{entry.media?.release_date?.slice(0, 4)} · {entry.media?.genres?.[0] ?? entry.media?.media_type}</p></div><span className={`status-mark status-mark--${entry.status}`}>{entry.status.replace("_", " ")}</span><strong>{entry.manual_rating?.toFixed(1) ?? "—"}</strong><strong>{entry.arena ? entry.arena.battle_score.toFixed(1) : "—"}</strong></article>)}</section>}
  </div>;
}

function RatingMeta({ entry }: { entry: LibraryItem }) {
  return <div className="library-card__meta"><span className={`status-mark status-mark--${entry.status}`}>{entry.status.replace("_", " ")}</span><span>{entry.manual_rating ? `My rating ${entry.manual_rating.toFixed(1)}` : "My rating —"}</span><span>{entry.arena ? `Arena ${entry.arena.battle_score.toFixed(1)}${entry.arena.provisional ? " provisional" : ""}` : "Arena —"}</span></div>;
}

function compareEntries(left: LibraryItem, right: LibraryItem, sort: SortOption) {
  if (sort === "updated") return right.updated_at.localeCompare(left.updated_at);
  const isArena = sort.startsWith("arena");
  const leftValue = isArena ? left.arena?.battle_score : left.manual_rating;
  const rightValue = isArena ? right.arena?.battle_score : right.manual_rating;
  if (leftValue == null) return rightValue == null ? 0 : 1;
  if (rightValue == null) return -1;
  return sort.endsWith("desc") ? rightValue - leftValue : leftValue - rightValue;
}
