"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BookmarkPlus, Sparkles } from "lucide-react";

import { MediaCard } from "@/components/media-card";
import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { MediaSummary, Page } from "@/lib/types";

export default function RecommendationsPage() {
  const recommendations = useQuery({ queryKey: ["recommendations", "movie"], queryFn: () => apiRequest<Page<MediaSummary>>("/recommendations/movie") });
  return <div className="page-stack">
    <PageHeader eyebrow="For you" title="A considered next pick." description="Recommendations are transparent: they use the genres and ratings already present in your own archive." />
    <section className="recommendation-intro"><Sparkles size={19} /><p><strong>Based on your completed thrillers and highly rated science fiction.</strong> This is a catalog-based starting point, not a black box.</p></section>
    <section className="media-grid">{recommendations.data?.items.map((media) => <div className="recommendation-card" key={media.media_id}><MediaCard media={media} /><div className="recommendation-card__reason"><span>Why this surfaced</span><p>Shares genre signals with titles you rated 7.0 or higher.</p><button className="text-link"><BookmarkPlus size={15} /> Add to planned</button></div></div>)}</section>
    <section className="panel source-note"><div><p className="eyebrow">Recommendation inputs</p><h2>Your data stays legible.</h2></div><ul><li>Favourites and ratings you entered</li><li>Completed media and shared genres</li><li>Available public ratings as a tie-breaker</li></ul><a href="/settings">Manage preferences <ArrowUpRight size={15} /></a></section>
  </div>;
}
