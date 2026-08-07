"use client";

import { useQueries } from "@tanstack/react-query";
import { useMemo } from "react";

import { apiRequest } from "@/lib/api";
import type { MediaSummary } from "@/lib/types";

export function useMediaMap(mediaIds: string[]) {
  const uniqueIds = useMemo(() => [...new Set(mediaIds)], [mediaIds]);
  const queries = useQueries({
    queries: uniqueIds.map((mediaId) => ({
      queryKey: ["media", mediaId],
      queryFn: () => apiRequest<MediaSummary>(`/media/${mediaId}`),
      staleTime: 5 * 60_000,
    })),
  });

  return useMemo(
    () => new Map(queries.flatMap((query, index) => query.data ? [[uniqueIds[index], query.data] as const] : [])),
    [queries, uniqueIds],
  );
}
