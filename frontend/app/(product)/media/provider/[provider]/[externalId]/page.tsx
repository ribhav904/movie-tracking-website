"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";

import { MediaDetailView } from "@/components/media-detail-view";
import { apiRequest } from "@/lib/api";
import type { MediaDetail, MediaType } from "@/lib/types";

const mediaTypes = new Set<MediaType>(["movie", "tv", "game", "book"]);

export default function ProviderMediaDetailPage() {
  const params = useParams<{ provider: string; externalId: string }>();
  const searchParams = useSearchParams();
  const requestedType = searchParams.get("media_type");
  const mediaType = mediaTypes.has(requestedType as MediaType) ? requestedType as MediaType : null;
  const media = useQuery({
    queryKey: ["provider-media", params.provider, params.externalId, mediaType],
    queryFn: () => apiRequest<MediaDetail>(`/media/provider/${encodeURIComponent(params.provider)}/${encodeURIComponent(params.externalId)}?media_type=${mediaType}`),
    enabled: mediaType !== null,
  });

  if (!mediaType) return <Unavailable />;
  if (media.isLoading) return <div className="screen-loader">Opening title…</div>;
  if (!media.data || media.isError) return <Unavailable />;
  return <MediaDetailView item={media.data} />;
}

function Unavailable() {
  return <div className="empty-state"><div><h3>This title is unavailable.</h3><Link href="/discover" className="text-link">Return to discover</Link></div></div>;
}
