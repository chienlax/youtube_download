/**
 * Custom hook to manage a download via SSE progress streaming.
 * Sends POST /api/download, then opens an EventSource to /api/download/progress/<id>.
 */

import { useState, useCallback, useRef } from "react";
import type { DownloadProgress, DownloadMode } from "../types";

const API = "http://127.0.0.1:5000";

interface UseDownloadReturn {
  progress: DownloadProgress | null;
  isDownloading: boolean;
  startDownload: (params: {
    url: string;
    formatId: string | null;
    mode: DownloadMode;
    subtitles: string[];
    title: string;
    thumbnail: string | null;
  }) => void;
  reset: () => void;
}

export function useDownload(): UseDownloadReturn {
  const [progress, setProgress] = useState<DownloadProgress | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }
    setProgress(null);
    setIsDownloading(false);
  }, []);

  const startDownload = useCallback(
    async (params: {
      url: string;
      formatId: string | null;
      mode: DownloadMode;
      subtitles: string[];
      title: string;
      thumbnail: string | null;
    }) => {
      reset();
      setIsDownloading(true);

      try {
        const res = await fetch(`${API}/api/download`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(params),
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.error || "Download request failed");

        const downloadId = data.downloadId;

        // Open SSE stream
        const es = new EventSource(
          `${API}/api/download/progress/${downloadId}`
        );
        esRef.current = es;

        es.onmessage = (event) => {
          try {
            const state: DownloadProgress = JSON.parse(event.data);
            setProgress(state);

            if (state.status === "completed" || state.status === "failed") {
              es.close();
              esRef.current = null;
              setIsDownloading(false);
            }
          } catch {
            // ignore parse errors
          }
        };

        es.onerror = () => {
          es.close();
          esRef.current = null;
          setIsDownloading(false);
        };
      } catch (err) {
        setProgress({
          status: "failed",
          progress: 0,
          speed: "",
          eta: "",
          filename: "",
          error: err instanceof Error ? err.message : "Unknown error",
        });
        setIsDownloading(false);
      }
    },
    [reset]
  );

  return { progress, isDownloading, startDownload, reset };
}
