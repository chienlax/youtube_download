import type { VideoFormat } from "../types";

interface FormatPickerProps {
  formats: VideoFormat[];
  selectedFormatId: string | null;
  onSelect: (formatId: string | null) => void;
}

export default function FormatPicker({
  formats,
  selectedFormatId,
  onSelect,
}: FormatPickerProps) {
  return (
    <div className="format-picker">
      <label className="picker-label" htmlFor="format-select">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <polygon points="23 7 16 12 23 17 23 7" />
          <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
        </svg>
        Resolution
      </label>
      <select
        id="format-select"
        className="picker-select"
        value={selectedFormatId ?? "best"}
        onChange={(e) =>
          onSelect(e.target.value === "best" ? null : e.target.value)
        }
      >
        <option value="best">Best Available</option>
        {formats.map((f) => (
          <option key={f.formatId} value={f.formatId}>
            {f.display}
          </option>
        ))}
      </select>
    </div>
  );
}
