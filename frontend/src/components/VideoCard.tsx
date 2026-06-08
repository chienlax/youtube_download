import type { VideoInfo } from "../types";

interface VideoCardProps {
  info: VideoInfo;
}

function formatDuration(seconds: number | null): string {
  if (!seconds) return "—";
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

export default function VideoCard({ info }: VideoCardProps) {
  return (
    <div className="video-card">
      {info.thumbnail && (
        <div className="video-card-thumb">
          <img
            src={info.thumbnail}
            alt={info.title}
            loading="lazy"
          />
          <span className="video-card-duration">
            {formatDuration(info.duration)}
          </span>
        </div>
      )}
      <div className="video-card-info">
        <h2 className="video-card-title" title={info.title}>
          {info.title}
        </h2>
        <div className="video-card-meta">
          <span className="video-card-channel">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
              <circle cx="12" cy="7" r="4" />
            </svg>
            {info.channel}
          </span>
          <span className="video-card-duration-text">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            {info.durationString}
          </span>
          <span className="video-card-formats">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polygon points="23 7 16 12 23 17 23 7" />
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
            </svg>
            {info.formats.length} formats
          </span>
          {info.subtitles.length > 0 && (
            <span className="video-card-subs">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              {info.subtitles.length} subs
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
