"use client";
/* eslint-disable @next/next/no-img-element */

import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, BookmarkPlus, CalendarDays, Star } from "lucide-react";
import Link from "next/link";

import { useParams } from "next/navigation";

import { apiRequest } from "@/lib/api";
import type { MediaSummary } from "@/lib/types";

export default function MediaDetailPage() {
  const params = useParams<{ mediaId: string }>();
  const media = useQuery({ queryKey: ["media", params.mediaId], queryFn: () => apiRequest<MediaSummary>(`/media/${params.mediaId}`) });
  if (media.isLoading) return <div className="screen-loader">Opening title…</div>;
  if (!media.data) return <div className="empty-state"><div><h3>This title is unavailable.</h3><Link href="/discover" className="text-link">Return to discover</Link></div></div>;
  const item = media.data;
  return <div className="media-detail"><Link className="back-link" href="/discover"><ArrowLeft size={16} /> Discover</Link><div className={`media-detail__cover media-detail__cover--${item.media_type}`}>{item.poster_url ? <img src={item.poster_url} alt="" /> : <span>{item.title.slice(0, 1)}</span>}</div><section className="media-detail__main"><p className="eyebrow">{item.media_type} · {item.release_date?.slice(0, 4) ?? "Unscheduled"}</p><h1>{item.title}</h1><p className="media-detail__description">{item.description}</p><div className="detail-meta"><span><CalendarDays size={16} /> {item.release_date ?? "Release date unavailable"}</span>{item.public_rating && <span><Star size={16} fill="currentColor" /> {item.public_rating.normalized_10.toFixed(1)} <small>{item.public_rating.source}</small></span>}</div><div className="detail-actions"><button className="button button--primary"><BookmarkPlus size={16} /> Add to library</button><button className="button button--secondary">Mark as watched</button></div></section></div>;
}
