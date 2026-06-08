import { useState, useEffect, useCallback } from "react";
import type { HistoryEntry } from "../types";

const API = "http://127.0.0.1:5000";

export default function HistoryPanel() {
  const [entries, setEntries] = useState<HistoryEntry[]>([]);
  const [isOpen, setIsOpen] = useState(false);

  const refresh = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/history`);
      if (res.ok) {
        const data = await res.json();
        setEntries(data);
      }
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    refresh();
    // Refresh every 10 seconds to catch completed downloads
    const interval = setInterval(refresh, 10000);
    return () => clearInterval(interval);
  }, [refresh]);

  const handleDelete = async (id: string) => {
    await fetch(`${API}/api/history/${id}`, { method: "DELETE" });
    refresh();
  };

  const handleClear = async () => {
    await fetch(`${API}/api/history`, { method: "DELETE" });
    refresh();
  };

  const formatDate = (iso: string) => {
    const d = new Date(iso);
    return d.toLocaleString();
  };

  return (
    <div className="history-panel">
      <button
        className="history-toggle"
        onClick={() => {
          setIsOpen(!isOpen);
          if (!isOpen) refresh();
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
        Download History ({entries.length})
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className={`chevron ${isOpen ? "open" : ""}`}
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      {isOpen && (
        <div className="history-content">
          {entries.length === 0 ? (
            <p className="history-empty">No downloads yet.</p>
          ) : (
            <>
              <div className="history-actions">
                <button
                  className="btn btn-ghost btn-sm"
                  onClick={handleClear}
                >
                  Clear All
                </button>
              </div>
              <div className="history-list">
                {entries.map((entry) => (
                  <div key={entry.id} className="history-item">
                    {entry.thumbnail && (
                      <img
                        src={entry.thumbnail}
                        alt=""
                        className="history-thumb"
                        loading="lazy"
                      />
                    )}
                    <div className="history-item-info">
                      <span className="history-item-title" title={entry.title}>
                        {entry.title}
                      </span>
                      <span className="history-item-meta">
                        <span
                          className={`status-badge ${entry.status}`}
                        >
                          {entry.status}
                        </span>
                        <span className="history-item-mode">
                          {entry.mode === "audio" ? "🎵 MP3" : "🎬 Video"}
                        </span>
                        <span className="history-item-date">
                          {formatDate(entry.timestamp)}
                        </span>
                      </span>
                    </div>
                    <button
                      className="btn btn-ghost btn-icon"
                      onClick={() => handleDelete(entry.id)}
                      title="Remove from history"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
