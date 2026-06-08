import { useState, useRef, useEffect } from "react";

interface UrlInputProps {
  onFetch: (url: string) => void;
  isLoading: boolean;
  disabled: boolean;
}

export default function UrlInput({ onFetch, isLoading, disabled }: UrlInputProps) {
  const [url, setUrl] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = url.trim();
    if (trimmed) onFetch(trimmed);
  };

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        onFetch(text.trim());
      }
    } catch {
      // Clipboard permission denied — user can paste manually
    }
  };

  return (
    <form className="url-input-form" onSubmit={handleSubmit}>
      <div className="url-input-wrapper">
        <div className="url-input-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
            <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
          </svg>
        </div>
        <input
          ref={inputRef}
          id="url-input"
          type="text"
          className="url-input"
          placeholder="Paste a YouTube video URL here..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={disabled}
          autoComplete="off"
          spellCheck={false}
        />
        <button
          type="button"
          className="btn btn-ghost"
          onClick={handlePaste}
          disabled={disabled}
          title="Paste from clipboard"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
          </svg>
        </button>
      </div>
      <button
        type="submit"
        className="btn btn-primary"
        disabled={!url.trim() || isLoading || disabled}
        id="fetch-btn"
      >
        {isLoading ? (
          <span className="spinner" />
        ) : (
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <polyline points="21 8 21 21 3 21 3 8" />
            <rect x="1" y="3" width="22" height="5" />
            <line x1="10" y1="12" x2="14" y2="12" />
          </svg>
        )}
        Fetch
      </button>
    </form>
  );
}
