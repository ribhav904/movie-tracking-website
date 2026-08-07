"use client";

import { useQuery } from "@tanstack/react-query";

import { ActivityHeatmap } from "@/components/activity-heatmap";
import { PageHeader } from "@/components/page-header";
import { apiRequest } from "@/lib/api";
import type { ReportSummary, YearReport } from "@/lib/types";

export default function ReportsPage() {
  const report = useQuery({ queryKey: ["reports", 2026], queryFn: () => apiRequest<YearReport>("/reports/year/2026") });
  const summary = useQuery({ queryKey: ["reports", "summary"], queryFn: () => apiRequest<ReportSummary>("/reports/summary") });
  return <div className="page-stack">
    <PageHeader eyebrow="2026 in review" title="A year measured by attention." description="Your report is built from the dates you chose, not a streak you are expected to protect." actions={<select className="select-control" defaultValue="2026" aria-label="Report year"><option>2026</option><option>2025</option></select>} />
    <section className="report-metrics"><Metric label="Recorded entries" value={report.data?.total_events ?? 0} /><Metric label="Active days" value={report.data?.active_days ?? 0} /><Metric label="Completed" value={report.data?.completed_items ?? 0} /><Metric label="Personal average" value={summary.data?.average_manual_rating?.toFixed(1) ?? "—"} suffix="/10" /></section>
    <section className="panel report-calendar"><div className="section-heading"><div><p className="eyebrow">Daily history</p><h2>The rhythm of the year</h2></div><span className="result-count">{report.data?.active_days ?? 0} active days</span></div>{report.data && <ActivityHeatmap year={report.data.year} calendar={report.data.calendar} />}</section>
    <section className="panel report-notes"><p className="eyebrow">What this report is for</p><h2>Remember the shape of your year.</h2><p>Use the calendar to find a particular stretch of time. Use the totals to notice patterns. Neither one is a scorecard.</p><p className="muted-copy">Breakdowns by media type, favourite rate, session duration, and activity runs will appear only after the backend exposes those calculated metrics.</p></section>
  </div>;
}

function Metric({ label, value, suffix }: { label: string; value: string | number; suffix?: string }) { return <div><span>{label}</span><strong>{value}<small>{suffix}</small></strong></div>; }
