"use client";
/* eslint-disable @next/next/no-img-element */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, BookmarkCheck, BookmarkPlus, CalendarDays, Check, Pencil, RotateCcw, Star, Trash2, X } from "lucide-react";
import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

import { ApiError, apiRequest } from "@/lib/api";
import type { Consumption, LibraryEntry, MediaDetail, Page, SeasonSummary } from "@/lib/types";

type CompletionTarget = { season?: SeasonSummary } | null;
type DateMode = "today" | "specific" | "unknown";

export function MediaDetailView({ item }: { item: MediaDetail }) {
  const queryClient = useQueryClient();
  const [target, setTarget] = useState<CompletionTarget>(null);
  const [editing, setEditing] = useState<Consumption | null>(null);
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiRequest<Page<LibraryEntry>>("/library?limit=100") });
  const entry = library.data?.items.find((candidate) => candidate.media_id === item.media_id);
  const records = useQuery({
    queryKey: ["consumptions", entry?.id],
    queryFn: () => apiRequest<Consumption[]>(`/library/${entry?.id}/consumptions`),
    enabled: Boolean(entry),
  });
  const seasons = useQuery({
    queryKey: ["seasons", item.media_id],
    queryFn: () => apiRequest<SeasonSummary[]>(`/media/${item.media_id}/seasons`),
    enabled: item.media_type === "tv" && Boolean(item.media_id),
  });

  const refresh = async () => {
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["library"] }),
      queryClient.invalidateQueries({ queryKey: ["consumptions"] }),
      queryClient.invalidateQueries({ queryKey: ["seasons", item.media_id] }),
      queryClient.invalidateQueries({ queryKey: ["history"] }),
      queryClient.invalidateQueries({ queryKey: ["reports"] }),
      queryClient.invalidateQueries({ queryKey: ["summary"] }),
    ]);
  };
  const addMutation = useMutation({
    mutationFn: () => ensureLibraryEntry(item, library.data?.items ?? []),
    onSuccess: refresh,
  });
  const deleteMutation = useMutation({
    mutationFn: (record: Consumption) => apiRequest<void>(`/consumptions/${record.id}`, { method: "DELETE", headers: { "Idempotency-Key": crypto.randomUUID() } }),
    onSuccess: refresh,
  });
  const error = addMutation.error ?? deleteMutation.error;
  const actionLabel = item.media_type === "movie" ? "watched" : item.media_type === "game" ? "completed" : "read";
  const recordsBySeason = useMemo(() => new Map(records.data?.map((record) => [record.season_id, record]) ?? []), [records.data]);

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
        {item.media_type !== "tv" && <button className="button button--secondary" disabled={!item.media_id} onClick={() => setTarget({})}>
          {entry && (records.data?.length ?? 0) > 0 ? <RotateCcw size={16} /> : <Check size={16} />} {entry && (records.data?.length ?? 0) > 0 ? `Log another ${actionLabel}` : `Mark as ${actionLabel}`}
        </button>}
      </div>
      {addMutation.isSuccess && <p className="action-message" role="status">Added to your library. Log a completion whenever you are ready.</p>}
      {error && <p className="form-error" role="alert">{error instanceof Error ? error.message : "The change could not be saved."}</p>}
    </section>

    {item.media_type === "tv" && <section className="completion-section panel">
      <div className="section-heading"><div><p className="eyebrow">Season tracking</p><h2>Watch a show season by season.</h2></div></div>
      {!entry && <p className="muted-copy">Add this show to your library first. The arena still rates the show as one whole title.</p>}
      {entry && <div className="season-list">{seasons.data?.filter((season) => season.season_number > 0).map((season) => {
        const last = recordsBySeason.get(season.id);
        return <article className="season-row" key={season.id}><div><strong>{season.title ?? `Season ${season.season_number}`}</strong><p>{season.watched_count ? `${season.watched_count} watch${season.watched_count === 1 ? "" : "es"}${season.latest_rating ? ` · ${season.latest_rating}/10` : ""}` : "Not logged yet"}</p></div><button className="button button--secondary" onClick={() => setTarget({ season })}>{last ? <><RotateCcw size={16} /> Rewatch</> : <><Check size={16} /> Mark watched</>}</button></article>;
      })}</div>}
    </section>}

    {entry && <section className="completion-section panel">
      <div className="section-heading"><div><p className="eyebrow">Your record</p><h2>Completed {records.data?.length ?? 0} time{(records.data?.length ?? 0) === 1 ? "" : "s"}.</h2></div></div>
      {records.data?.length ? <ol className="completion-history">{records.data.map((record) => <li key={record.id}><div><strong>{record.season_id ? `Season ${seasons.data?.find((season) => season.id === record.season_id)?.season_number ?? ""}` : `Completion ${record.sequence_number}`}</strong><p>{record.completed_on ? new Date(`${record.completed_on}T00:00:00`).toLocaleDateString() : "Previously completed — date unknown"}{record.rating ? ` · ${record.rating}/10` : ""}</p>{record.notes && <p className="completion-history__notes">{record.notes}</p>}</div><div className="record-actions"><button className="icon-button" aria-label="Edit completion" onClick={() => setEditing(record)}><Pencil size={15} /></button><button className="icon-button" aria-label="Delete completion" onClick={() => { if (window.confirm("Delete this completion record?")) deleteMutation.mutate(record); }}><Trash2 size={15} /></button></div></li>)}</ol> : <p className="muted-copy">This title is in your library but has not been completed yet.</p>}
    </section>}
    {(target || editing) && <CompletionForm item={item} entry={entry} target={target} record={editing} onClose={() => { setTarget(null); setEditing(null); }} onSaved={refresh} />}
  </div>;
}

function CompletionForm({ item, entry, target, record, onClose, onSaved }: { item: MediaDetail; entry?: LibraryEntry; target: CompletionTarget; record: Consumption | null; onClose: () => void; onSaved: () => Promise<void> }) {
  const [dateMode, setDateMode] = useState<DateMode>(record?.completed_on ? "specific" : "today");
  const [date, setDate] = useState(record?.completed_on ?? localDate(new Date()));
  const [rating, setRating] = useState(record?.rating?.toString() ?? "");
  const [notes, setNotes] = useState(record?.notes ?? "");
  const save = useMutation({
    mutationFn: async () => {
      const libraryEntry = entry ?? await ensureLibraryEntry(item, [], "planned");
      const payload = { completed_on: dateMode === "unknown" ? null : dateMode === "today" ? localDate(new Date()) : date, rating: rating ? Number(rating) : null, notes: notes.trim() || null, ...(target?.season ? { season_id: target.season.id } : {}) };
      return apiRequest<Consumption>(record ? `/consumptions/${record.id}` : `/library/${libraryEntry.id}/consumptions`, { method: record ? "PATCH" : "POST", body: JSON.stringify(payload), headers: { "Idempotency-Key": crypto.randomUUID() } });
    },
    onSuccess: async () => { await onSaved(); onClose(); },
  });
  const label = target?.season ? target.season.title ?? `Season ${target.season.season_number}` : item.title;
  return <div className="modal-backdrop" role="presentation"><section className="completion-modal panel" role="dialog" aria-modal="true" aria-labelledby="completion-title"><div className="activity-form__heading"><div><p className="eyebrow">{record ? "Edit completion" : "Log completion"}</p><h2 id="completion-title">{label}</h2></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close form"><X size={18} /></button></div><form onSubmit={(event: FormEvent<HTMLFormElement>) => { event.preventDefault(); save.mutate(); }}>
    <fieldset><legend>When did you finish it?</legend><label><input type="radio" checked={dateMode === "today"} onChange={() => setDateMode("today")} /> Today</label><label><input type="radio" checked={dateMode === "specific"} onChange={() => setDateMode("specific")} /> On a specific date</label><label><input type="radio" checked={dateMode === "unknown"} onChange={() => setDateMode("unknown")} /> In the past, date unknown</label></fieldset>
    {dateMode === "specific" && <label>Date<input type="date" value={date} onChange={(event) => setDate(event.target.value)} required /></label>}
    <label>Your rating <span className="field-note">Optional, from 1–10 in 0.5 steps</span><input type="number" min="1" max="10" step="0.5" value={rating} onChange={(event) => setRating(event.target.value)} /></label>
    <label>Thoughts <textarea rows={5} maxLength={20000} value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="What stayed with you?" /></label>
    {save.error && <p className="form-error" role="alert">{save.error instanceof Error ? save.error.message : "Could not save this completion."}</p>}
    <div className="activity-form__actions"><button type="button" className="button button--quiet" onClick={onClose}>Cancel</button><button className="button button--primary" type="submit" disabled={save.isPending}>{save.isPending ? "Saving…" : "Save completion"}</button></div>
  </form></section></div>;
}

async function ensureLibraryEntry(item: MediaDetail, entries: LibraryEntry[], status: LibraryEntry["status"] = "planned") {
  if (!item.media_id) throw new ApiError("This title has not been imported yet.", 422, "MEDIA_NOT_IMPORTED");
  const existing = entries.find((entry) => entry.media_id === item.media_id);
  if (existing) return existing;
  try {
    return await apiRequest<LibraryEntry>("/library", { method: "POST", body: JSON.stringify({ media_id: item.media_id, status }), headers: { "Idempotency-Key": crypto.randomUUID() } });
  } catch (error) {
    if (!(error instanceof ApiError) || error.code !== "LIBRARY_ENTRY_EXISTS") throw error;
    const refreshed = await apiRequest<Page<LibraryEntry>>("/library?limit=100");
    const concurrent = refreshed.items.find((candidate) => candidate.media_id === item.media_id);
    if (!concurrent) throw error;
    return concurrent;
  }
}

function localDate(value: Date) {
  const offset = value.getTimezoneOffset();
  return new Date(value.getTime() - offset * 60_000).toISOString().slice(0, 10);
}
