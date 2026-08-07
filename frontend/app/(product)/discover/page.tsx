"use client";

import { useQuery } from "@tanstack/react-query";
import { Check, LoaderCircle, Search, SlidersHorizontal } from "lucide-react";
import { useMemo, useState } from "react";

import { MediaCard } from "@/components/media-card";
import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { MediaSummary, MediaType, Page } from "@/lib/types";

const mediaTypes: Array<{ value: MediaType; label: string }> = [
  { value: "movie", label: "Films" },
  { value: "tv", label: "Television" },
  { value: "game", label: "Games" },
  { value: "book", label: "Books" },
];

export default function DiscoverPage() {
  const [mediaType, setMediaType] = useState<MediaType>("movie");
  const [search, setSearch] = useState("");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [minimumRating, setMinimumRating] = useState(0);
  const path = useMemo(() => search.trim() ? `/media/search?media_type=${mediaType}&query=${encodeURIComponent(search.trim())}&page=1` : `/media/discover?media_type=${mediaType}&page=1`, [mediaType, search]);
  const results = useQuery({ queryKey: ["discover", mediaType, search], queryFn: () => apiRequest<Page<MediaSummary>>(path) });
  const visibleResults = useMemo(() => (results.data?.items ?? []).filter((item) => (item.public_rating?.normalized_10 ?? 0) >= minimumRating), [minimumRating, results.data]);
  const typeLabel = mediaTypes.find((item) => item.value === mediaType)?.label.toLowerCase();

  return <div className="page-stack">
    <PageHeader eyebrow="Explore" title="Find something worth your time." description="Search provider-backed catalogs, then add only the items that belong in your archive." />
    <section className="discover-toolbar">
      <div className="segmented-control" aria-label="Media type">{mediaTypes.map((item) => <button key={item.value} className={mediaType === item.value ? "is-active" : ""} onClick={() => setMediaType(item.value)}>{item.label}</button>)}</div>
      <label className="search-field"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${typeLabel}`} /></label>
      <button className="button button--secondary filter-button" aria-expanded={filtersOpen} onClick={() => setFiltersOpen((open) => !open)}><SlidersHorizontal size={16} /> Filters</button>
    </section>
    {filtersOpen && <section className="discover-filters panel"><label>Minimum public rating<select value={minimumRating} onChange={(event) => setMinimumRating(Number(event.target.value))}><option value="0">Any rating</option><option value="6">6.0 and above</option><option value="7">7.0 and above</option><option value="8">8.0 and above</option><option value="9">9.0 and above</option></select></label><button className="button button--quiet" onClick={() => setMinimumRating(0)}>Clear filters</button></section>}
    <section className="content-section">
      <div className="section-heading"><div><p className="eyebrow">{search ? `Results for “${search}”` : "A starting point"}</p><h2>{search ? "Matches from your selected source" : `Explore ${typeLabel}`}</h2></div><span className="result-count">{visibleResults.length} items</span></div>
      {results.isLoading ? <div className="loading-state"><LoaderCircle className="spin" size={20} /> Finding titles…</div> : <div className="media-grid">{visibleResults.map((media) => <MediaCard key={`${media.provider}-${media.external_id}`} media={media} />)}</div>}
      {!results.isLoading && !visibleResults.length && <div className="empty-state"><span><Check size={19} /></span><div><h3>No matches here yet.</h3><p>Try a different title, source category, or a broader search.</p></div></div>}
    </section>
  </div>;
}
