"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CalendarDays, Clock3, FileText, Plus, X } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { Activity, ActivityCreate, LibraryEntry, Page } from "@/lib/types";
import { useMediaMap } from "@/lib/use-media-map";

type FormValues = ActivityCreate & { entry_id: string; rating?: number };

export default function ActivityPage() {
  const queryClient = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const activity = useQuery({ queryKey: ["activity", 100], queryFn: () => apiRequest<Page<Activity>>("/activity?limit=100") });
  const library = useQuery({ queryKey: ["library"], queryFn: () => apiRequest<Page<LibraryEntry>>("/library?limit=100") });
  const mediaIds = useMemo(() => [...(activity.data?.items.map((item) => item.media_id) ?? []), ...(library.data?.items.map((item) => item.media_id) ?? [])], [activity.data, library.data]);
  const mediaMap = useMediaMap(mediaIds);
  const logMutation = useMutation({
    mutationFn: async ({ entry_id, rating, ...payload }: FormValues) => {
      if (payload.kind === "rated" && rating !== undefined) {
        await apiRequest<LibraryEntry>(`/library/${entry_id}`, { method: "PATCH", body: JSON.stringify({ manual_rating: rating }) });
      }
      return apiRequest<Activity>(`/library/${entry_id}/events`, {
        method: "POST",
        body: JSON.stringify(payload),
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
    },
    onSuccess: async () => {
      setFormOpen(false);
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["activity"] }),
        queryClient.invalidateQueries({ queryKey: ["library"] }),
        queryClient.invalidateQueries({ queryKey: ["reports"] }),
      ]);
    },
  });

  useEffect(() => {
    const openFromHash = () => {
      if (window.location.hash === "#log") setFormOpen(true);
    };
    openFromHash();
    window.addEventListener("hashchange", openFromHash);
    return () => window.removeEventListener("hashchange", openFromHash);
  }, []);

  const openForm = () => {
    setFormOpen(true);
    window.history.replaceState(null, "", "#log");
    requestAnimationFrame(() => document.getElementById("log")?.scrollIntoView({ behavior: "smooth", block: "center" }));
  };
  const closeForm = () => {
    setFormOpen(false);
    window.history.replaceState(null, "", window.location.pathname);
  };

  return <div className="page-stack">
    <PageHeader eyebrow="The record" title="Every session has a place." description="Keep exact timestamps for detail and local activity dates for an honest yearly record." actions={<button className="button button--primary" onClick={openForm}><Plus size={16} /> Log activity</button>} />
    {formOpen && <ActivityForm entries={library.data?.items ?? []} mediaMap={mediaMap} pending={logMutation.isPending} error={logMutation.error} onClose={closeForm} onSubmit={(values) => logMutation.mutate(values)} />}
    <div className="activity-layout">
      <section className="timeline panel"><div className="section-heading"><div><p className="eyebrow">Latest entries</p><h2>Your timeline</h2></div><span className="result-count">{activity.data?.items.length ?? 0} entries</span></div>
        {activity.data?.items.length ? <ol className="timeline__list">{activity.data.items.map((item) => <li key={item.id}><time><strong>{new Date(`${item.occurred_on}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</strong><small>{item.occurred_on.slice(0, 4)}</small></time><span className="timeline__line" /><article><div className="timeline__kind"><Clock3 size={15} />{kindLabel(item.kind)}</div><h3>{mediaMap.get(item.media_id)?.title ?? "Loading title…"}</h3><p>{item.notes ?? detailLabel(item)}</p></article></li>)}</ol> : <div className="empty-state"><div><h3>No activity logged yet.</h3><p>Add a title to your library, then record your first session.</p></div></div>}
      </section>
      <aside className="activity-aside"><section className="panel"><p className="eyebrow">A better log</p><h2>Record what changed.</h2><p className="muted-copy">Log a session, progress change, completion, rating, or note against any title in your library.</p><button className="button button--secondary" onClick={openForm}><FileText size={16} /> Open activity form</button></section><section className="activity-note"><CalendarDays size={18} /><p>Use the date you experienced it, even if you log it later. Your year view uses that local date.</p></section></aside>
    </div>
  </div>;
}

function ActivityForm({ entries, mediaMap, pending, error, onClose, onSubmit }: { entries: LibraryEntry[]; mediaMap: Map<string, { title: string }>; pending: boolean; error: Error | null; onClose: () => void; onSubmit: (values: FormValues) => void }) {
  const [kind, setKind] = useState<Activity["kind"]>("session");
  const today = localDate(new Date());
  const submit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const occurredOn = String(data.get("occurred_on"));
    const duration = optionalNumber(data.get("duration_minutes"));
    const progress = optionalNumber(data.get("progress_after"));
    const rating = optionalNumber(data.get("rating"));
    const notes = String(data.get("notes") ?? "").trim();
    onSubmit({
      entry_id: String(data.get("entry_id")),
      kind,
      occurred_on: occurredOn,
      occurred_at: localNoon(occurredOn).toISOString(),
      duration_minutes: duration,
      progress_after: progress,
      notes: notes || null,
      rating,
    });
  };

  return <section id="log" className="activity-form panel" aria-labelledby="activity-form-title">
    <div className="activity-form__heading"><div><p className="eyebrow">New entry</p><h2 id="activity-form-title">Log activity</h2></div><button type="button" className="icon-button" onClick={onClose} aria-label="Close activity form"><X size={18} /></button></div>
    {entries.length ? <form onSubmit={submit}>
      <label>Title<select name="entry_id" required defaultValue=""><option value="" disabled>Select from your library</option>{entries.map((entry) => <option value={entry.id} key={entry.id}>{mediaMap.get(entry.media_id)?.title ?? "Loading title…"}</option>)}</select></label>
      <label>Activity type<select value={kind} onChange={(event) => setKind(event.target.value as Activity["kind"])}><option value="session">Session</option><option value="progress">Progress update</option><option value="completed">Completed</option><option value="rated">Rating</option><option value="note">Note</option></select></label>
      <label>Date<input name="occurred_on" type="date" required defaultValue={today} /></label>
      {kind === "session" && <label>Duration in minutes<input name="duration_minutes" type="number" min="0" max="100000" inputMode="numeric" placeholder="For example, 45" /></label>}
      {kind === "progress" && <label>Progress<input name="progress_after" type="number" min="0" step="0.01" placeholder="Page, episode, or percent" /></label>}
      {kind === "rated" && <label>Rating out of 10<input name="rating" type="number" min="1" max="10" step="0.5" required /></label>}
      <label className="activity-form__notes">Notes<textarea name="notes" rows={4} maxLength={20000} placeholder="Optional context you want to remember" /></label>
      {error && <p className="form-error" role="alert">{error.message}</p>}
      <div className="activity-form__actions"><button type="button" className="button button--quiet" onClick={onClose}>Cancel</button><button type="submit" className="button button--primary" disabled={pending}>{pending ? "Saving…" : "Save activity"}</button></div>
    </form> : <div className="empty-state"><div><h3>Your library is empty.</h3><p>Add a movie, show, game, or book before logging activity.</p></div></div>}
  </section>;
}

function kindLabel(kind: Activity["kind"]) { return ({ started: "Started", session: "Session", progress: "Progress", episode_watched: "Episode watched", completed: "Completed", note: "Note", rated: "Rating" })[kind]; }
function detailLabel(item: Activity) { return item.duration_minutes ? `${item.duration_minutes} minute session` : item.progress_after !== null && item.progress_after !== undefined ? `${item.progress_after} progress` : "Recorded activity"; }
function optionalNumber(value: FormDataEntryValue | null) { const text = String(value ?? "").trim(); return text ? Number(text) : undefined; }
function localDate(value: Date) { const offset = value.getTimezoneOffset(); return new Date(value.getTime() - offset * 60_000).toISOString().slice(0, 10); }
function localNoon(date: string) { return new Date(`${date}T12:00:00`); }
