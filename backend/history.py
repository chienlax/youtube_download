"""
Download history manager.
Persists a list of past downloads as a JSON file in the data/ directory.
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
HISTORY_FILE = PROJECT_ROOT / "data" / "download_history.json"


def _load() -> list[dict]:
    """Load history from disk."""
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _save(entries: list[dict]) -> None:
    """Persist history to disk."""
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")


def get_all() -> list[dict]:
    """Return all history entries, newest first."""
    entries = _load()
    entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
    return entries


def add_entry(
    title: str,
    url: str,
    filename: str,
    status: str = "completed",
    mode: str = "video",
    thumbnail: str | None = None,
) -> dict:
    """Add a new history entry and return it."""
    entry = {
        "id": uuid.uuid4().hex[:12],
        "title": title,
        "url": url,
        "filename": filename,
        "status": status,
        "mode": mode,
        "thumbnail": thumbnail,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    entries = _load()
    entries.append(entry)
    _save(entries)
    return entry


def delete_entry(entry_id: str) -> bool:
    """Delete a history entry by id. Returns True if found and removed."""
    entries = _load()
    filtered = [e for e in entries if e.get("id") != entry_id]
    if len(filtered) == len(entries):
        return False
    _save(filtered)
    return True


def clear_all() -> None:
    """Remove all history entries."""
    _save([])
