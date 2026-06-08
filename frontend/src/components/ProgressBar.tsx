import type { DownloadProgress } from "../types";

interface ProgressBarProps {
  progress: DownloadProgress;
}

export default function ProgressBar({ progress }: ProgressBarProps) {
  const statusLabel: Record<string, string> = {
    starting: "Starting download…",
    downloading: "Downloading…",
    merging: "Merging audio & video…",
    completed: "Download complete! Paste a new URL above to continue.",
    failed: "Download failed",
  };

  return (
    <div className={`progress-section ${progress.status}`}>
      <div className="progress-header">
        <span className="progress-status">
          {progress.status === "completed" && (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          )}
          {progress.status === "failed" && (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <line x1="15" y1="9" x2="9" y2="15" />
              <line x1="9" y1="9" x2="15" y2="15" />
            </svg>
          )}
          {statusLabel[progress.status] || progress.status}
        </span>
      </div>

      <div className="progress-bar-track">
        <div
          className="progress-bar-fill"
          style={{ width: `${Math.min(progress.progress, 100)}%` }}
        />
      </div>

      <div className="progress-details">
        <span className="progress-pct">
          {progress.progress.toFixed(1)}%
        </span>
        {progress.speed && (
          <span className="progress-speed">{progress.speed}</span>
        )}
        {progress.eta && progress.eta !== "Unknown" && (
          <span className="progress-eta">ETA {progress.eta}</span>
        )}
      </div>

      {progress.filename && (
        <div className="progress-filename" title={progress.filename}>
          {progress.filename}
        </div>
      )}

      {progress.error && (
        <div className="progress-error">{progress.error}</div>
      )}
    </div>
  );
}
