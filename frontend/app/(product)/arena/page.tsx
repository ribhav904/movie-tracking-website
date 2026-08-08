"use client";

/* eslint-disable @next/next/no-img-element */

import { useMutation, useQueries, useQuery, useQueryClient } from "@tanstack/react-query";
import { Equal, Info, Trophy } from "lucide-react";
import { useState } from "react";

import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import { isBackendConfigured } from "@/lib/config";
import type { ArenaMatchup, MediaSummary, MediaType } from "@/lib/types";

const types: Array<{ value: MediaType; label: string }> = [
  { value: "movie", label: "Films" },
  { value: "tv", label: "Television" },
  { value: "game", label: "Games" },
  { value: "book", label: "Books" },
];

function matchupPath(mediaType: MediaType) {
  return `/arena/${mediaType}/matchup`;
}

export default function ArenaPage() {
  const [mediaType, setMediaType] = useState<MediaType>("movie");
  const queryClient = useQueryClient();
  const matchup = useQuery({
    queryKey: ["arena", mediaType, "matchup"],
    queryFn: () => apiRequest<ArenaMatchup>(matchupPath(mediaType)),
    enabled: isBackendConfigured,
    retry: false,
  });
  const comparison = useMutation({
    mutationFn: (outcome: "left" | "right" | "tie") =>
      apiRequest(`/arena/${mediaType}/comparisons`, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({
          left_media_id: matchup.data?.left_media_id,
          right_media_id: matchup.data?.right_media_id,
          outcome,
        }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["arena", mediaType] });
      // The next comparison is fetched immediately. The current cards remain
      // on screen until this one request resolves, avoiding a blank state.
      await queryClient.fetchQuery({
        queryKey: ["arena", mediaType, "matchup"],
        queryFn: () => apiRequest<ArenaMatchup>(matchupPath(mediaType)),
      });
    },
  });

  const changeType = (type: MediaType) => {
    setMediaType(type);
    comparison.reset();
  };
  const current = matchup.data;
  // A Vercel/Render rollout can briefly serve the previous matchup shape.
  // Fetch these only for that legacy response; normal Arena turns still use
  // the single enriched matchup request.
  const fallbackMedia = useQueries({
    queries: [current?.left_media_id, current?.right_media_id].map((mediaId) => ({
      queryKey: ["media", mediaId],
      queryFn: () => apiRequest<MediaSummary>(`/media/${mediaId}`),
      enabled: Boolean(current && mediaId && (!current.left_media || !current.right_media)),
      retry: false,
    })),
  });
  const leftMedia = current?.left_media ?? fallbackMedia[0].data;
  const rightMedia = current?.right_media ?? fallbackMedia[1].data;
  const loadingDetails = Boolean(current && (!leftMedia || !rightMedia) && fallbackMedia.some((query) => query.isLoading));
  const detailsError = Boolean(current && (!leftMedia || !rightMedia) && fallbackMedia.some((query) => query.isError));
  const isTransitioning = comparison.isPending || matchup.isFetching;

  return <div className="page-stack">
    <PageHeader eyebrow="Battle Arena" title="Which one stays with you?" description="Choose the title you prefer. Elo keeps the underlying comparison model; the displayed Battle Score expands your current Arena from 0 to 10." />
    <section className="arena-controls">
      <div className="segmented-control" aria-label="Arena media type">{types.map((type) => <button key={type.value} className={mediaType === type.value ? "is-active" : ""} onClick={() => changeType(type.value)} disabled={isTransitioning}>{type.label}</button>)}</div>
      <span><Info size={15} /> No repeated pairs · ties allowed</span>
    </section>
    {!isBackendConfigured ? <ArenaEmpty message="Connect FastAPI and sign in to begin an Arena. Comparisons are never simulated in preview mode." /> : null}
    {isBackendConfigured && ((matchup.isLoading && !current) || loadingDetails) ? <ArenaLoading /> : null}
    {isBackendConfigured && (matchup.isError || detailsError || (!matchup.isLoading && !current)) ? <ArenaEmpty message={detailsError ? "The pair was found, but its title details could not be loaded. Refresh and try again." : "There is no eligible unplayed pair yet. Complete at least two items of this type to begin."} /> : null}
    {current && leftMedia && rightMedia ? <>
      <section className={`arena-matchup ${isTransitioning ? "arena-matchup--submitting" : ""}`} aria-busy={isTransitioning}>
        <ArenaItem key={current.left_media_id} media={leftMedia} onChoose={() => comparison.mutate("left")} disabled={isTransitioning} />
        <div className="arena-matchup__middle"><span>or</span><button onClick={() => comparison.mutate("tie")} className="tie-button" aria-label="Choose a tie" disabled={isTransitioning}><Equal size={19} /></button><small>Tie</small></div>
        <ArenaItem key={current.right_media_id} media={rightMedia} onChoose={() => comparison.mutate("right")} disabled={isTransitioning} />
      </section>
      {comparison.isError ? <p className="muted-copy">This comparison could not be recorded. Your pair has not been changed; try again.</p> : null}
    </> : null}
    <section className="arena-footer panel"><div><Trophy size={18} /><p><strong>Battle Score is relative to this Arena</strong><br />Your current lowest Elo is shown as 0.0 and highest as 10.0. Tied Arenas remain at 5.0 until a result separates them.</p></div><span className="arena-footer__scale">Lowest 0.0 · Highest 10.0</span></section>
  </div>;
}

function ArenaLoading() { return <section className="arena-matchup arena-matchup--loading" aria-label="Finding an eligible pair"><div className="arena-item"><div className="arena-item__cover arena-item__cover--skeleton" /><div className="arena-item__text-skeleton" /><div className="arena-item__meta-skeleton" /></div><div className="arena-matchup__middle">Finding pair</div><div className="arena-item"><div className="arena-item__cover arena-item__cover--skeleton" /><div className="arena-item__text-skeleton" /><div className="arena-item__meta-skeleton" /></div></section>; }

function ArenaEmpty({ message }: { message: string }) { return <section className="panel empty-state"><div><h2>Arena is waiting for real entries.</h2><p>{message}</p></div></section>; }

function ArenaItem({ media, onChoose, disabled }: { media: MediaSummary; onChoose: () => void; disabled: boolean }) {
  const year = media.release_date ? new Date(media.release_date).getFullYear() : "—";
  return <article className="arena-item">
    <div className="arena-item__cover">{media.poster_url ? <img src={media.poster_url} alt={`Poster for ${media.title}`} /> : <span aria-hidden="true">{media.title.slice(0, 1)}</span>}</div>
    <p className="eyebrow">{year} · {media.genres?.[0] ?? media.media_type}</p>
    <h2 title={media.title}>{media.title}</h2>
    <dl><div><dt>Public rating</dt><dd>{media.public_rating?.normalized_10.toFixed(1) ?? "—"}</dd></div><div><dt>Decision</dt><dd>Choose one</dd></div></dl>
    <button className="button button--primary arena-item__choose" onClick={onChoose} disabled={disabled}>Choose this title</button>
  </article>;
}
