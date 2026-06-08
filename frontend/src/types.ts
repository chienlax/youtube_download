/**
 * TypeScript interfaces for the YouTube downloader app.
 */

export interface VideoFormat {
  formatId: string;
  height: number;
  fps: number;
  ext: string;
  vcodec: string;
  display: string;
}

export interface SubtitleTrack {
  code: string;
  auto: boolean;
}

export interface VideoInfo {
  id: string;
  title: string;
  thumbnail: string | null;
  duration: number | null;
  durationString: string;
  channel: string;
  url: string;
  formats: VideoFormat[];
  subtitles: SubtitleTrack[];
}

export interface DownloadProgress {
  status: "starting" | "downloading" | "merging" | "completed" | "failed";
  progress: number;
  speed: string;
  eta: string;
  filename: string;
  error: string | null;
}

export interface HistoryEntry {
  id: string;
  title: string;
  url: string;
  filename: string;
  status: string;
  mode: string;
  thumbnail: string | null;
  timestamp: string;
}

export type DownloadMode = "video" | "audio";

export type Theme = "dark" | "light";
