"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowUpRight, BookmarkCheck, BookmarkPlus, Sparkles } from "lucide-react";

import { MediaCard } from "@/components/media-card";
import { PageHeader } from "@/components/page-header";
import { ApiError, apiRequest } from "@/lib/api";
import type { LibraryEntry, MediaSummary, Page } from "@/lib/types";

export default function RecommendationsPage() {
  const queryClient = useQueryClient();
  const recommendations = useQuery({ queryKey: ["recommendations", "movie"], queryFn: () => apiRequest<Page<MediaSummary>>("/recommendations/movie") });
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiRequest<Page<LibraryEntry>>("/library?limit=100") });
  const add = useMutation({
    mutationFn: async (media: MediaSummary) => {
      if (!media.media_id) throw new ApiError("This recommendation is not available to add.", 422);
      return apiRequest<LibraryEntry>("/library", { method: "POST", body: JSON.stringify({ media_id: media.media_id, status: "planned" }), headers: { "Idempotency-Key": crypto.randomUUID() } });
    },
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["library"] }); },
  });

  return <div className="page-stack">
    <PageHeader eyebrow="For you" title="A considered next pick." description="Recommendations are transparent: they use the genres and ratings already present in your own archive." />
    <section className="recommendation-intro"><Sparkles size={19} /><p><strong>Based on your completed titles and personal ratings.</strong> This is a catalog-based starting point, not a black box.</p></section>
    {add.isError && <p className="form-error" role="alert">{add.error.message}</p>}
    <section className="media-grid">{recommendations.data?.items.map((media) => {
      const saved = library.data?.items.some((entry) => entry.media_id === media.media_id);
      return <div className="recommendation-card" key={media.media_id}><MediaCard media={media} /><div className="recommendation-card__reason"><span>Why this surfaced</span><p>Shares genre signals with titles you rated 7.0 or higher.</p><button className="text-link" disabled={saved || add.isPending} onClick={() => add.mutate(media)}>{saved ? <><BookmarkCheck size={15} /> In your library</> : <><BookmarkPlus size={15} /> Add to planned</>}</button></div></div>;
    })}</section>
    <section className="panel source-note"><div><p className="eyebrow">Recommendation inputs</p><h2>Your data stays legible.</h2></div><ul><li>Favourites and ratings you entered</li><li>Completed media and shared genres</li><li>Available public ratings as a tie-breaker</li></ul><a href="/settings">Manage preferences <ArrowUpRight size={15} /></a></section>
  </div>;
}
