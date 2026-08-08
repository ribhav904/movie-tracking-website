"use client";

import { useQuery } from "@tanstack/react-query";
import { Check, ChevronLeft, ChevronRight, LoaderCircle, Search, SlidersHorizontal } from "lucide-react";
import { Suspense, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";

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
const discoverModes = [
  { value: "trending", label: "Trending" },
  { value: "popular", label: "Popular" },
  { value: "top_rated", label: "Top rated" },
  { value: "recent", label: "New releases" },
] as const;
type DiscoverMode = (typeof discoverModes)[number]["value"];

export default function DiscoverPage() {
  return <Suspense fallback={<div className="loading-state"><LoaderCircle className="spin" size={20} /> Preparing discovery…</div>}><DiscoverContent /></Suspense>;
}

function DiscoverContent() {
  const searchParams = useSearchParams();
  const topSearch = searchParams.get("query") ?? "";
  const topScope = searchParams.get("scope") === "all";
  return <DiscoverSession key={`${topScope}:${topSearch}`} topSearch={topSearch} topScope={topScope} />;
}

function DiscoverSession({ topSearch, topScope }: { topSearch: string; topScope: boolean }) {
  const [mediaType, setMediaType] = useState<MediaType>("movie");
  const [draftSearch, setDraftSearch] = useState(topSearch);
  const [submittedSearch, setSubmittedSearch] = useState(topSearch);
  const [allMedia, setAllMedia] = useState(topScope && Boolean(topSearch));
  const [discoverMode, setDiscoverMode] = useState<DiscoverMode>("trending");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [minimumRating, setMinimumRating] = useState(0);
  const [page, setPage] = useState(1);

  const path = useMemo(() => {
    if (submittedSearch) {
      const scope = allMedia ? "" : `&media_type=${mediaType}`;
      return `/media/search?query=${encodeURIComponent(submittedSearch)}${scope}&page=${page}`;
    }
    return `/media/discover?media_type=${mediaType}&mode=${discoverMode}&page=${page}`;
  }, [allMedia, discoverMode, mediaType, page, submittedSearch]);
  const results = useQuery({ queryKey: ["discover", mediaType, submittedSearch, allMedia, discoverMode, page], queryFn: () => apiRequest<Page<MediaSummary>>(path) });
  const visibleResults = useMemo(() => (results.data?.items ?? []).filter((item) => (item.public_rating?.normalized_10 ?? 0) >= minimumRating), [minimumRating, results.data]);
  const typeLabel = mediaTypes.find((item) => item.value === mediaType)?.label.toLowerCase();
  const heading = allMedia ? "Matches across films, television, games, and books" : submittedSearch ? "Matches from your selected source" : `Explore ${typeLabel}`;

  return <div className="page-stack">
    <PageHeader eyebrow="Explore" title="Find something worth your time." description="Search provider-backed catalogs, then add only the items that belong in your archive." />
    <section className="discover-toolbar">
      <div className="segmented-control" aria-label="Media type">{mediaTypes.map((item) => <button key={item.value} className={!allMedia && mediaType === item.value ? "is-active" : ""} onClick={() => { setMediaType(item.value); setSubmittedSearch(""); setDraftSearch(""); setAllMedia(false); setPage(1); }}>{item.label}</button>)}</div>
      <form className="search-field" onSubmit={(event) => { event.preventDefault(); setSubmittedSearch(draftSearch.trim()); setAllMedia(false); setPage(1); }}><Search size={18} /><input value={draftSearch} onChange={(event) => setDraftSearch(event.target.value)} placeholder={`Search ${typeLabel}`} /><button className="search-submit" type="submit">Search</button></form>
      <button className="button button--secondary filter-button" aria-expanded={filtersOpen} onClick={() => setFiltersOpen((open) => !open)}><SlidersHorizontal size={16} /> Filters</button>
    </section>
    {!submittedSearch && <section className="discover-mode"><label>Browse by<select value={discoverMode} onChange={(event) => { setDiscoverMode(event.target.value as DiscoverMode); setPage(1); }}>{discoverModes.map((mode) => <option key={mode.value} value={mode.value}>{mode.label}</option>)}</select></label><p>{discoverMode === "recent" ? "Recently released titles where the provider supports them." : "Provider-supported discovery lists, updated with each request."}</p></section>}
    {allMedia && <section className="global-search-note"><strong>All media search</strong><span>Results are balanced across the four catalogues.</span></section>}
    {filtersOpen && <section className="discover-filters panel"><label>Minimum public rating<select value={minimumRating} onChange={(event) => setMinimumRating(Number(event.target.value))}><option value="0">Any rating</option><option value="6">6.0 and above</option><option value="7">7.0 and above</option><option value="8">8.0 and above</option><option value="9">9.0 and above</option></select></label><button className="button button--quiet" onClick={() => setMinimumRating(0)}>Clear filters</button></section>}
    <section className="content-section">
      <div className="section-heading"><div><p className="eyebrow">{submittedSearch ? `Results for “${submittedSearch}”` : discoverModes.find((mode) => mode.value === discoverMode)?.label}</p><h2>{heading}</h2></div><span className="result-count">{visibleResults.length} items</span></div>
      {results.isLoading ? <div className="loading-state"><LoaderCircle className="spin" size={20} /> Finding titles…</div> : <div className="media-grid">{visibleResults.map((media) => <MediaCard key={`${media.provider}-${media.external_id}`} media={media} />)}</div>}
      {!results.isLoading && !visibleResults.length && <div className="empty-state"><span><Check size={19} /></span><div><h3>No matches here yet.</h3><p>Try a different title, source category, or a broader search.</p></div></div>}
      <nav className="pagination" aria-label="Discovery results pages"><button className="button button--secondary" disabled={page === 1 || results.isFetching} onClick={() => setPage((current) => current - 1)}><ChevronLeft size={16} /> Previous</button><span>Page {page}</span><button className="button button--secondary" disabled={!results.data?.next_cursor || results.isFetching} onClick={() => setPage((current) => current + 1)}>Next <ChevronRight size={16} /></button></nav>
    </section>
  </div>;
}
