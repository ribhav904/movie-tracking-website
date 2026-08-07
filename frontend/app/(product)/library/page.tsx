"use client";

import { useQuery } from "@tanstack/react-query";
import { Heart, LayoutGrid, Rows3, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { MediaCard } from "@/components/media-card";
import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { LibraryEntry, LibraryStatus, Page } from "@/lib/types";
import { useMediaMap } from "@/lib/use-media-map";

const statuses: Array<{ value: "all" | LibraryStatus; label: string }> = [
  { value: "all", label: "Everything" }, { value: "in_progress", label: "In progress" }, { value: "planned", label: "Planned" }, { value: "completed", label: "Completed" }, { value: "paused", label: "Paused" },
];

export default function LibraryPage() {
  const [status, setStatus] = useState<"all" | LibraryStatus>("all");
  const [search, setSearch] = useState("");
  const [view, setView] = useState<"grid" | "list">("grid");
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiRequest<Page<LibraryEntry>>("/library?limit=100") });
  const mediaMap = useMediaMap(library.data?.items.map((entry) => entry.media_id) ?? []);
  const entries = useMemo(() => (library.data?.items ?? []).map((entry) => ({ ...entry, media: entry.media ?? mediaMap.get(entry.media_id) })).filter((entry) => (status === "all" || entry.status === status) && (!search || entry.media?.title.toLowerCase().includes(search.toLowerCase()))), [library.data, mediaMap, search, status]);

  return <div className="page-stack">
    <PageHeader eyebrow="Your archive" title="A library that remembers context." description="Status, personal notes, and three kinds of rating live alongside every title." />
    <section className="library-toolbar">
      <div className="status-tabs">{statuses.map((item) => <button key={item.value} className={status === item.value ? "is-active" : ""} onClick={() => setStatus(item.value)}>{item.label}</button>)}</div>
      <div className="toolbar-actions"><label className="search-field search-field--small"><Search size={16} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Filter your library" /></label><div className="view-switch"><button className={view === "grid" ? "is-active" : ""} aria-label="Grid view" onClick={() => setView("grid")}><LayoutGrid size={16} /></button><button className={view === "list" ? "is-active" : ""} aria-label="List view" onClick={() => setView("list")}><Rows3 size={16} /></button></div></div>
    </section>
    {view === "grid" ? <section className="media-grid">{entries.map((entry) => entry.media && <div className="library-card" key={entry.id}><MediaCard media={entry.media} /><div className="library-card__meta"><span className={`status-mark status-mark--${entry.status}`}>{entry.status.replace("_", " ")}</span><span>{entry.manual_rating ? `${entry.manual_rating.toFixed(1)} personal` : "Not rated"}</span>{entry.favorite && <Heart size={14} fill="currentColor" aria-label="Favourite" />}</div></div>)}</section> : <section className="library-list">{entries.map((entry) => <article key={entry.id} className="library-list__row"><span className={`type-dot type-dot--${entry.media?.media_type}`} /><div><h3>{entry.media?.title}</h3><p>{entry.media?.release_date?.slice(0, 4)} · {entry.media?.genres?.[0] ?? entry.media?.media_type}</p></div><span className={`status-mark status-mark--${entry.status}`}>{entry.status.replace("_", " ")}</span><strong>{entry.manual_rating?.toFixed(1) ?? "—"}</strong></article>)}</section>}
  </div>;
}
