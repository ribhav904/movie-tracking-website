"use client";

import { useQuery } from "@tanstack/react-query";
import { CalendarDays, Star } from "lucide-react";
import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { HistoryItem, Page } from "@/lib/types";

export default function HistoryPage() {
  const history = useQuery({ queryKey: ["history", 100], queryFn: () => apiRequest<Page<HistoryItem>>("/history?limit=100") });
  return <div className="page-stack">
    <PageHeader eyebrow="Your archive" title="Completion history." description="Only dated finishes appear here. Past completions with an unknown date stay in the title record without changing your reports." />
    <section className="timeline panel"><div className="section-heading"><div><p className="eyebrow">Latest finishes</p><h2>Your timeline</h2></div><span className="result-count">{history.data?.items.length ?? 0} entries</span></div>
      {history.data?.items.length ? <ol className="timeline__list">{history.data.items.map((item) => <li key={item.id}><time><strong>{new Date(`${item.completed_on}T00:00:00`).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</strong><small>{item.completed_on?.slice(0, 4)}</small></time><span className="timeline__line" /><article><div className="timeline__kind"><CalendarDays size={15} /> Completed</div><h3><Link href={`/media/${item.media_id}`}>{item.title}</Link>{item.season_number ? ` · Season ${item.season_number}` : ""}</h3><p>{item.rating ? <><Star size={12} fill="currentColor" /> {item.rating}/10</> : "No personal rating"}</p>{item.notes && <p>{item.notes}</p>}</article></li>)}</ol> : <div className="empty-state"><div><h3>No dated completions yet.</h3><p>Mark a title complete from its page, then choose today or a specific date.</p></div></div>}
    </section>
  </div>;
}
