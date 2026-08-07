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
  const path = useMemo(() => {
    if (!search.trim()) return `/media/discover?media_type=${mediaType}&page=1`;
    return `/media/search?media_type=${mediaType}&query=${encodeURIComponent(search.trim())}&page=1`;
  }, [mediaType, search]);
  const results = useQuery({ queryKey: ["discover", mediaType, search], queryFn: () => apiRequest<Page<MediaSummary>>(path) });

  return <div className="page-stack">
    <PageHeader eyebrow="Explore" title="Find something worth your time." description="Search provider-backed catalogs, then add only the items that belong in your archive." />
    <section className="discover-toolbar">
      <div className="segmented-control" aria-label="Media type">
        {mediaTypes.map((item) => <button key={item.value} className={mediaType === item.value ? "is-active" : ""} onClick={() => setMediaType(item.value)}>{item.label}</button>)}
      </div>
      <label className="search-field"><Search size={18} /><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder={`Search ${mediaTypes.find((item) => item.value === mediaType)?.label.toLowerCase()}`} /><kbd>Enter</kbd></label>
      <button className="button button--secondary filter-button"><SlidersHorizontal size={16} /> Filters</button>
    </section>
    <section className="content-section">
      <div className="section-heading"><div><p className="eyebrow">{search ? `Results for “${search}”` : "A starting point"}</p><h2>{search ? "Matches from your selected source" : `Explore ${mediaTypes.find((item) => item.value === mediaType)?.label.toLowerCase()}`}</h2></div><span className="result-count">{results.data?.items.length ?? 0} items</span></div>
      {results.isLoading ? <div className="loading-state"><LoaderCircle className="spin" size={20} /> Finding titles…</div> : <div className="media-grid">{results.data?.items.map((media) => <MediaCard key={`${media.provider}-${media.external_id}`} media={media} />)}</div>}
      {!results.isLoading && !results.data?.items.length && <div className="empty-state"><span><Check size={19} /></span><div><h3>No matches here yet.</h3><p>Try a different title, source category, or a broader search.</p></div></div>}
    </section>
  </div>;
}
