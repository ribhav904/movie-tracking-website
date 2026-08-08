/* eslint-disable @next/next/no-img-element */

import { BookOpen, Clapperboard, Gamepad2, MonitorPlay, Star } from "lucide-react";
import Link from "next/link";

import type { MediaSummary, MediaType } from "@/lib/types";

const typeIcon: Record<MediaType, typeof Clapperboard> = {
  movie: Clapperboard,
  tv: MonitorPlay,
  game: Gamepad2,
  book: BookOpen,
};

export function MediaCard({ media, compact = false }: { media: MediaSummary; compact?: boolean }) {
  const Icon = typeIcon[media.media_type];
  const year = media.release_date ? new Date(media.release_date).getFullYear() : null;
  const href = media.media_id
    ? `/media/${media.media_id}`
    : `/media/provider/${encodeURIComponent(media.provider)}/${encodeURIComponent(media.external_id)}?media_type=${media.media_type}`;
  return (
    <Link href={href} className={`media-card ${compact ? "media-card--compact" : ""}`}>
      <div className={`media-card__cover media-card__cover--${media.media_type}`}>
        {media.poster_url ? <img src={media.poster_url} alt={`${media.title} cover`} /> : <span>{media.title.slice(0, 1)}</span>}
        <div className="media-card__cover-meta"><Icon size={14} /> {media.media_type}</div>
      </div>
      <div className="media-card__body">
        <h3>{media.title}</h3>
        <p>{year ?? "Unscheduled"}{media.genres?.[0] ? ` · ${media.genres[0]}` : ""}</p>
        {media.public_rating && (
          <span className="rating-line"><Star size={13} fill="currentColor" /> {media.public_rating.normalized_10.toFixed(1)} <small>{media.public_rating.source}</small></span>
        )}
      </div>
    </Link>
  );
}
