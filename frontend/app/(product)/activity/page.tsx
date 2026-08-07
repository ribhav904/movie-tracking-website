"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Clock3, FileText, Plus } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { Activity, Page } from "@/lib/types";

export default function ActivityPage() {
  const activity = useQuery({ queryKey: ["activity", 100], queryFn: () => apiRequest<Page<Activity>>("/activity?limit=100") });
  return <div className="page-stack">
    <PageHeader eyebrow="The record" title="Every session has a place." description="Keep exact timestamps for detail and local activity dates for an honest yearly record." actions={<button className="button button--primary"><Plus size={16} /> Log activity</button>} />
    <div className="activity-layout">
      <section className="timeline panel"><div className="section-heading"><div><p className="eyebrow">Latest entries</p><h2>Your timeline</h2></div><span className="result-count">{activity.data?.items.length ?? 0} entries</span></div><ol className="timeline__list">{activity.data?.items.map((item) => <li key={item.id}><time><strong>{new Date(item.occurred_on).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</strong><small>{new Date(item.occurred_on).getFullYear()}</small></time><span className="timeline__line" /><article><div className="timeline__kind"><Clock3 size={15} />{kindLabel(item.kind)}</div><h3>{item.media?.title ?? "Library item"}</h3><p>{item.notes ?? detailLabel(item)}</p></article></li>)}</ol></section>
      <aside className="activity-aside"><section className="panel"><p className="eyebrow">A better log</p><h2>Record what changed.</h2><p className="muted-copy">A quick entry can be a session, episode, progress change, completion, rating, or note. The active title chooser appears here when your FastAPI data is connected.</p><button className="button button--secondary"><FileText size={16} /> Open activity form</button></section><section className="activity-note"><CalendarDays size={18} /><p>Use the date you experienced it, even if you log it later. Your year view uses that local date.</p></section></aside>
    </div>
  </div>;
}

function kindLabel(kind: Activity["kind"]) { return ({ session: "Session", progress: "Progress", episode_watched: "Episode watched", completed: "Completed", note: "Note", rating: "Rating" })[kind]; }
function detailLabel(item: Activity) { return item.duration_minutes ? `${item.duration_minutes} minute session` : item.progress_after ? `${item.progress_after}% progress` : "Recorded activity"; }
