"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { MediaDetailView } from "@/components/media-detail-view";
import { apiRequest } from "@/lib/api";
import type { MediaDetail } from "@/lib/types";

export default function MediaDetailPage() {
  const params = useParams<{ mediaId: string }>();
  const media = useQuery({ queryKey: ["media", params.mediaId], queryFn: () => apiRequest<MediaDetail>(`/media/${params.mediaId}/details`) });
  if (media.isLoading) return <div className="screen-loader">Opening title…</div>;
  if (!media.data) return <div className="empty-state"><div><h3>This title is unavailable.</h3><Link href="/discover" className="text-link">Return to discover</Link></div></div>;
  return <MediaDetailView item={media.data} />;
}
