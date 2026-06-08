import { useState, useCallback, useEffect } from "react";
import Header from "./components/Header";
import UrlInput from "./components/UrlInput";
import VideoCard from "./components/VideoCard";
import FormatPicker from "./components/FormatPicker";
import SubtitlePicker from "./components/SubtitlePicker";
import DownloadButton from "./components/DownloadButton";
import ProgressBar from "./components/ProgressBar";
import HistoryPanel from "./components/HistoryPanel";
import { useDownload } from "./hooks/useDownload";
import type { VideoInfo, DownloadMode, Theme } from "./types";

const API = "http://127.0.0.1:5000";

function getInitialTheme(): Theme {
  const saved = localStorage.getItem("theme");
  if (saved === "light" || saved === "dark") return saved;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

/**
 * Find the best English subtitle code from available subtitles.
 * Prefers original "en" over auto-generated, falls back to any "en*" variant.
 */
function findEnglishSub(
  subtitles: { code: string; auto: boolean }[]
): string | null {
  // 1. Exact "en" manual sub
  const enManual = subtitles.find((s) => s.code === "en" && !s.auto);
  if (enManual) return enManual.code;

  // 2. Exact "en" auto sub
  const enAuto = subtitles.find((s) => s.code === "en" && s.auto);
  if (enAuto) return enAuto.code;

  // 3. Any "en-*" variant (en-US, en-GB, etc.)
  const enVariant = subtitles.find((s) => s.code.startsWith("en"));
  if (enVariant) return enVariant.code;

  return null;
}

export default function App() {
  // Theme
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () =>
    setTheme((prev) => (prev === "dark" ? "light" : "dark"));

  // Video state
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null);
  const [isFetching, setIsFetching] = useState(false);
  const [fetchError, setFetchError] = useState<string | null>(null);

  // Options state
  const [selectedFormatId, setSelectedFormatId] = useState<string | null>(null);
  const [mode, setMode] = useState<DownloadMode>("video");

  // Selected subtitle codes
  const [selectedSubtitles, setSelectedSubtitles] = useState<string[]>([]);

  // Download
  const { progress, isDownloading, startDownload, reset } = useDownload();

  const handleFetch = useCallback(
    async (url: string) => {
      // Reset any previous download progress so UI is fresh
      reset();

      setIsFetching(true);
      setFetchError(null);
      setVideoInfo(null);
      setSelectedFormatId(null);
      setSelectedSubtitles([]);

      try {
        const res = await fetch(
          `${API}/api/info?url=${encodeURIComponent(url)}`
        );
        const data = await res.json();

        if (!res.ok)
          throw new Error(data.error || "Failed to fetch video info");

        setVideoInfo(data);

        // Auto-detect English subtitles
        const enCode = findEnglishSub(data.subtitles || []);
        if (enCode) {
          setSelectedSubtitles([enCode]);
        }
      } catch (err) {
        setFetchError(
          err instanceof Error ? err.message : "An unknown error occurred"
        );
      } finally {
        setIsFetching(false);
      }
    },
    [reset]
  );

  const handleDownload = useCallback(() => {
    if (!videoInfo) return;

    const selectedFormat = videoInfo.formats.find(
      (f) => f.formatId === selectedFormatId
    );
    const mergeFormat = selectedFormat ? selectedFormat.ext : null;

    startDownload({
      url: videoInfo.url,
      formatId: mode === "audio" ? null : selectedFormatId,
      mode,
      subtitles: selectedSubtitles,
      title: videoInfo.title,
      thumbnail: videoInfo.thumbnail,
      mergeFormat,
    });
  }, [videoInfo, selectedFormatId, mode, selectedSubtitles, startDownload]);

  return (
    <>
      <Header theme={theme} onToggleTheme={toggleTheme} />

      <main className="app-main">
        <UrlInput
          onFetch={handleFetch}
          isLoading={isFetching}
          disabled={isDownloading}
        />

        {fetchError && (
          <div className="error-banner">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {fetchError}
          </div>
        )}

        {videoInfo && (
          <>
            <VideoCard info={videoInfo} />

            <div className="options-row">
              <FormatPicker
                formats={videoInfo.formats}
                selectedFormatId={selectedFormatId}
                onSelect={setSelectedFormatId}
              />

              <SubtitlePicker
                subtitles={videoInfo.subtitles || []}
                selected={selectedSubtitles}
                onChange={setSelectedSubtitles}
              />
            </div>

            {progress ? (
              <ProgressBar progress={progress} />
            ) : (
              <DownloadButton
                mode={mode}
                onModeChange={setMode}
                onDownload={handleDownload}
                disabled={isDownloading}
              />
            )}
          </>
        )}

        <HistoryPanel />
      </main>
    </>
  );
}
