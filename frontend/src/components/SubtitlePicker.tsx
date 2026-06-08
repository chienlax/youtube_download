import { useState } from "react";
import type { SubtitleTrack } from "../types";

interface SubtitlePickerProps {
  subtitles: SubtitleTrack[];
  selected: string[];
  onChange: (selected: string[]) => void;
}

export default function SubtitlePicker({
  subtitles,
  selected,
  onChange,
}: SubtitlePickerProps) {
  const [expanded, setExpanded] = useState(false);

  if (subtitles.length === 0) return null;

  // Show manual subs first, then auto-generated
  const manual = subtitles.filter((s) => !s.auto);
  const auto = subtitles.filter((s) => s.auto);
  const sorted = [...manual, ...auto];

  // Limit visible to 8 unless expanded
  const visible = expanded ? sorted : sorted.slice(0, 8);
  const hasMore = sorted.length > 8;

  const toggle = (code: string) => {
    if (selected.includes(code)) {
      onChange(selected.filter((c) => c !== code));
    } else {
      onChange([...selected, code]);
    }
  };

  return (
    <div className="subtitle-picker">
      <label className="picker-label">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
        </svg>
        Subtitles ({subtitles.length} available)
      </label>
      <div className="subtitle-list">
        {visible.map((sub) => (
          <label
            key={sub.code}
            className={`subtitle-chip ${selected.includes(sub.code) ? "selected" : ""}`}
          >
            <input
              type="checkbox"
              checked={selected.includes(sub.code)}
              onChange={() => toggle(sub.code)}
            />
            <span className="subtitle-chip-code">{sub.code}</span>
            {sub.auto && <span className="subtitle-chip-auto">auto</span>}
          </label>
        ))}
      </div>
      {hasMore && (
        <button
          type="button"
          className="btn btn-ghost btn-sm"
          onClick={() => setExpanded(!expanded)}
        >
          {expanded ? "Show less" : `Show all ${sorted.length} languages`}
        </button>
      )}
    </div>
  );
}
