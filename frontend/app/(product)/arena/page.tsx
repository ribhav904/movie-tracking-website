"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
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

export default function ArenaPage() {
  const [mediaType, setMediaType] = useState<MediaType>("movie");
  const queryClient = useQueryClient();
  const matchup = useQuery({
    queryKey: ["arena", mediaType, "matchup"],
    queryFn: () => apiRequest<ArenaMatchup>(`/arena/${mediaType}/matchup`),
    enabled: isBackendConfigured,
    retry: false,
  });
  const left = useQuery({
    queryKey: ["media", matchup.data?.left_media_id],
    queryFn: () => apiRequest<MediaSummary>(`/media/${matchup.data?.left_media_id}`),
    enabled: Boolean(matchup.data?.left_media_id),
  });
  const right = useQuery({
    queryKey: ["media", matchup.data?.right_media_id],
    queryFn: () => apiRequest<MediaSummary>(`/media/${matchup.data?.right_media_id}`),
    enabled: Boolean(matchup.data?.right_media_id),
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
      await queryClient.invalidateQueries({ queryKey: ["arena", mediaType, "matchup"] });
    },
  });

  const changeType = (type: MediaType) => {
    setMediaType(type);
    comparison.reset();
  };

  return <div className="page-stack">
    <PageHeader eyebrow="Battle Arena" title="Which one stays with you?" description="A deliberate head-to-head comparison creates a Battle Score that remains separate from your manual and public ratings." />
    <section className="arena-controls"><div className="segmented-control">{types.map((type) => <button key={type.value} className={mediaType === type.value ? "is-active" : ""} onClick={() => changeType(type)}>{type.label}</button>)}</div><span><Info size={15} /> No repeated pairs · ties allowed</span></section>
    {!isBackendConfigured ? <ArenaEmpty message="Connect FastAPI and sign in to begin an Arena. Comparisons are never simulated in preview mode." /> : null}
    {isBackendConfigured && matchup.isLoading ? <ArenaEmpty message="Finding an eligible pair…" /> : null}
    {isBackendConfigured && (matchup.isError || !matchup.data || !left.data || !right.data) ? <ArenaEmpty message="There is no eligible unplayed pair yet. Complete at least two items of this type to begin." /> : null}
    {matchup.data && left.data && right.data ? <>
      <section className="arena-matchup">
        <ArenaItem side="left" media={left.data} onChoose={() => comparison.mutate("left")} disabled={comparison.isPending} />
        <div className="arena-matchup__middle"><span>or</span><button onClick={() => comparison.mutate("tie")} className="tie-button" aria-label="Choose a tie" disabled={comparison.isPending}><Equal size={19} /></button><small>Tie</small></div>
        <ArenaItem side="right" media={right.data} onChoose={() => comparison.mutate("right")} disabled={comparison.isPending} />
      </section>
      {comparison.isError ? <p className="muted-copy">This comparison could not be recorded. Refresh to get a current pairing.</p> : null}
    </> : null}
    <section className="arena-footer panel"><div><Trophy size={18} /><p><strong>Battle Score is provisional</strong><br />It settles after five comparisons. New titles begin at Elo 1500.</p></div></section>
  </div>;
}

function ArenaEmpty({ message }: { message: string }) { return <section className="panel empty-state"><div><h2>Arena is waiting for real entries.</h2><p>{message}</p></div></section>; }

function ArenaItem({ side, media, onChoose, disabled }: { side: "left" | "right"; media: MediaSummary; onChoose: () => void; disabled: boolean }) {
  const year = media.release_date ? new Date(media.release_date).getFullYear() : "—";
  return <article className={`arena-item arena-item--${side}`}><div className="arena-item__cover"><span>{media.title.slice(0, 1)}</span></div><p className="eyebrow">{year} · {media.genres?.[0] ?? media.media_type}</p><h2>{media.title}</h2><dl><div><dt>Public rating</dt><dd>{media.public_rating?.normalized_10.toFixed(1) ?? "—"}</dd></div></dl><button className="button button--secondary" onClick={onChoose} disabled={disabled}>This one</button></article>;
}
