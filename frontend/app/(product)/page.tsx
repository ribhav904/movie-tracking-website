"use client";

import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, CalendarDays, Check, Clock3, Plus, Sparkles } from "lucide-react";
import Link from "next/link";

import { ActivityHeatmap } from "@/components/activity-heatmap";
import { MediaCard } from "@/components/media-card";
import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { Activity, LibraryEntry, Page, ReportSummary, YearReport } from "@/lib/types";

export default function TodayPage() {
  const summary = useQuery({ queryKey: ["reports", "summary"], queryFn: () => apiRequest<ReportSummary>("/reports/summary") });
  const activity = useQuery({ queryKey: ["activity", 6], queryFn: () => apiRequest<Page<Activity>>("/activity?limit=6") });
  const library = useQuery({ queryKey: ["library", "current"], queryFn: () => apiRequest<Page<LibraryEntry>>("/library?limit=12") });
  const report = useQuery({ queryKey: ["report", 2026], queryFn: () => apiRequest<YearReport>("/reports/year/2026") });
  const current = library.data?.items.filter((entry) => entry.status === "in_progress") ?? [];

  return (
    <div className="page-stack">
      <PageHeader
        eyebrow="Friday, 7 August"
        title="Your collection, in motion."
        description="Pick up where you left off, record the small things, and keep the year in view."
        actions={<Link href="/discover" className="button button--secondary"><Plus size={16} /> Add to library</Link>}
      />

      <section className="metric-strip" aria-label="Collection summary">
        <div><span>In your library</span><strong>{summary.data?.library_items ?? "—"}</strong></div>
        <div><span>Completed</span><strong>{summary.data?.completed_items ?? "—"}</strong></div>
        <div><span>Personal average</span><strong>{summary.data?.average_manual_rating?.toFixed(1) ?? "—"}<small>/10</small></strong></div>
        <div><span>Favourites</span><strong>{summary.data?.favorites ?? "—"}</strong></div>
      </section>

      <section className="content-section">
        <div className="section-heading"><div><p className="eyebrow">In progress</p><h2>Continue your current runs</h2></div><Link href="/library?status=in_progress">See library <ArrowUpRight size={15} /></Link></div>
        {current.length ? <div className="media-grid media-grid--three">{current.map((entry) => entry.media && <MediaCard key={entry.id} media={entry.media} />)}</div> : <EmptyCurrent />}
      </section>

      <div className="dashboard-columns">
        <section className="content-section panel panel--heatmap">
          <div className="section-heading"><div><p className="eyebrow">The year so far</p><h2>Activity, not streaks</h2></div><Link href="/reports">Full report <ArrowUpRight size={15} /></Link></div>
          {report.data ? <ActivityHeatmap year={report.data.year} calendar={report.data.calendar} /> : <div className="skeleton-block" />}
          <p className="muted-copy">{report.data?.active_days ?? 0} days with an intentional entry. A quieter week still belongs here.</p>
        </section>

        <section className="content-section panel recent-panel">
          <div className="section-heading"><div><p className="eyebrow">Recently recorded</p><h2>Latest activity</h2></div><Link href="/activity">All activity <ArrowUpRight size={15} /></Link></div>
          <ol className="activity-list">
            {(activity.data?.items ?? []).slice(0, 4).map((item) => <li key={item.id}><span className="activity-list__icon"><Clock3 size={15} /></span><div><strong>{item.media?.title ?? "Library item"}</strong><p>{activityLabel(item)}</p></div><time>{new Date(item.occurred_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</time></li>)}
          </ol>
        </section>
      </div>

      <section className="quiet-callout">
        <div className="quiet-callout__icon"><Sparkles size={19} /></div>
        <div><p className="eyebrow">Battle Arena</p><h2>Your completed films are ready for a better question.</h2><p>Choose between two at a time. The Arena builds a separate, evolving Battle Score from your comparisons.</p></div>
        <Link href="/arena" className="button button--secondary">Enter Arena</Link>
      </section>
    </div>
  );
}

function activityLabel(item: Activity) {
  if (item.kind === "completed") return "Marked complete";
  if (item.kind === "episode_watched") return item.notes ?? "Episode watched";
  if (item.kind === "rating") return item.notes ?? "Updated rating";
  return item.duration_minutes ? `${item.duration_minutes} minute session` : "Activity recorded";
}

function EmptyCurrent() {
  return <div className="empty-state"><span><CalendarDays size={19} /></span><div><h3>Nothing is currently in progress.</h3><p>Start a film, series, game, or book from your library when you are ready.</p></div><Link className="text-link" href="/library">Open library <Check size={15} /></Link></div>;
}
