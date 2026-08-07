"use client";
/* eslint-disable @next/next/no-img-element */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BookmarkCheck, BookmarkPlus, CalendarDays, Check, Star } from "lucide-react";
import Link from "next/link";

import { ApiError, apiRequest } from "@/lib/api";
import type { Activity, ActivityCreate, LibraryEntry, MediaSummary, Page } from "@/lib/types";

export function MediaDetailView({ item }: { item: MediaSummary }) {
  const queryClient = useQueryClient();
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiRequest<Page<LibraryEntry>>("/library?limit=100") });
  const entry = library.data?.items.find((candidate) => candidate.media_id === item.media_id);

  const addMutation = useMutation({
    mutationFn: () => ensureLibraryEntry(item, library.data?.items ?? [], "planned"),
    onSuccess: async () => { await queryClient.invalidateQueries({ queryKey: ["library"] }); },
  });
  const watchedMutation = useMutation({
    mutationFn: async () => {
      const libraryEntry = await ensureLibraryEntry(item, library.data?.items ?? [], "in_progress");
      const now = new Date();
      const payload: ActivityCreate = {
        kind: "completed",
        occurred_at: now.toISOString(),
        occurred_on: localDate(now),
      };
      return apiRequest<Activity>(`/library/${libraryEntry.id}/events`, {
        method: "POST",
        body: JSON.stringify(payload),
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["library"] }),
        queryClient.invalidateQueries({ queryKey: ["activity"] }),
        queryClient.invalidateQueries({ queryKey: ["reports"] }),
      ]);
    },
  });
  const error = addMutation.error ?? watchedMutation.error;

  return <div className="media-detail">
    <Link className="back-link" href="/discover"><ArrowLeft size={16} /> Discover</Link>
    <div className={`media-detail__cover media-detail__cover--${item.media_type}`}>{item.poster_url ? <img src={item.poster_url} alt={`${item.title} cover`} /> : <span>{item.title.slice(0, 1)}</span>}</div>
    <section className="media-detail__main">
      <p className="eyebrow">{item.media_type} · {item.release_date?.slice(0, 4) ?? "Unscheduled"}</p>
      <h1>{item.title}</h1>
      <p className="media-detail__description">{item.description}</p>
      <div className="detail-meta"><span><CalendarDays size={16} /> {item.release_date ?? "Release date unavailable"}</span>{item.public_rating && <span><Star size={16} fill="currentColor" /> {item.public_rating.normalized_10.toFixed(1)} <small>{item.public_rating.source}</small></span>}</div>
      <div className="detail-actions">
        <button className="button button--primary" disabled={Boolean(entry) || addMutation.isPending} onClick={() => addMutation.mutate()}>
          {entry ? <><BookmarkCheck size={16} /> In your library</> : <><BookmarkPlus size={16} /> {addMutation.isPending ? "Adding…" : "Add to library"}</>}
        </button>
        <button className="button button--secondary" disabled={watchedMutation.isPending} onClick={() => watchedMutation.mutate()}>
          <Check size={16} /> {watchedMutation.isPending ? "Saving…" : entry?.status === "completed" ? "Log another watch" : "Mark as watched"}
        </button>
      </div>
      {watchedMutation.isSuccess && <p className="action-message" role="status">Watch logged. This title is now in your activity and yearly report.</p>}
      {addMutation.isSuccess && !watchedMutation.isSuccess && <p className="action-message" role="status">Added to your library.</p>}
      {error && <p className="form-error" role="alert">{error instanceof Error ? error.message : "The change could not be saved."}</p>}
    </section>
  </div>;
}

async function ensureLibraryEntry(item: MediaSummary, entries: LibraryEntry[], status: LibraryEntry["status"]) {
  if (!item.media_id) throw new ApiError("This title has not been imported yet.", 422, "MEDIA_NOT_IMPORTED");
  const existing = entries.find((entry) => entry.media_id === item.media_id);
  if (existing) return existing;
  try {
    return await apiRequest<LibraryEntry>("/library", {
      method: "POST",
      body: JSON.stringify({ media_id: item.media_id, status }),
      headers: { "Idempotency-Key": crypto.randomUUID() },
    });
  } catch (error) {
    if (!(error instanceof ApiError) || error.code !== "LIBRARY_ENTRY_EXISTS") throw error;
    const refreshed = await apiRequest<Page<LibraryEntry>>("/library?limit=100");
    const concurrent = refreshed.items.find((entry) => entry.media_id === item.media_id);
    if (!concurrent) throw error;
    return concurrent;
  }
}

function localDate(value: Date) {
  const offset = value.getTimezoneOffset();
  return new Date(value.getTime() - offset * 60_000).toISOString().slice(0, 10);
}
