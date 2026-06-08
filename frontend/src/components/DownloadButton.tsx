import type { DownloadMode } from "../types";

interface DownloadButtonProps {
  mode: DownloadMode;
  onModeChange: (mode: DownloadMode) => void;
  onDownload: () => void;
  disabled: boolean;
}

export default function DownloadButton({
  mode,
  onModeChange,
  onDownload,
  disabled,
}: DownloadButtonProps) {
  return (
    <div className="download-actions">
      <div className="mode-toggle">
        <button
          type="button"
          className={`mode-btn ${mode === "video" ? "active" : ""}`}
          onClick={() => onModeChange("video")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polygon points="23 7 16 12 23 17 23 7" />
            <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
          </svg>
          Video
        </button>
        <button
          type="button"
          className={`mode-btn ${mode === "audio" ? "active" : ""}`}
          onClick={() => onModeChange("audio")}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 18V5l12-2v13" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
          Audio (MP3)
        </button>
      </div>

      <button
        type="button"
        className="btn btn-download"
        onClick={onDownload}
        disabled={disabled}
        id="download-btn"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="7 10 12 15 17 10" />
          <line x1="12" y1="15" x2="12" y2="3" />
        </svg>
        Download {mode === "audio" ? "MP3" : "Video"}
      </button>
    </div>
  );
}
