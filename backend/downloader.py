"""
yt-dlp wrapper module.
Handles metadata fetching, format parsing, subtitle discovery, and download execution
with real-time progress parsing.
"""

import json
import os
import re
import shutil
import subprocess
import uuid
from pathlib import Path
from threading import Thread

# Resolve project root (one level up from backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ---------------------------------------------------------------------------
# yt-dlp / ffmpeg detection
# ---------------------------------------------------------------------------

def _find_yt_dlp() -> str:
    """Locate the yt-dlp executable, preferring the bundled copy."""
    bundled = PROJECT_ROOT / "yt-dlp.exe"
    if bundled.exists():
        return str(bundled)
    found = shutil.which("yt-dlp") or shutil.which("yt-dlp.exe")
    if found:
        return found
    raise FileNotFoundError("yt-dlp executable not found")


def _find_ffmpeg() -> str | None:
    """Locate ffmpeg, preferring the bundled copy."""
    # Search for any ffmpeg-* directory in project root
    for entry in PROJECT_ROOT.iterdir():
        if entry.is_dir() and entry.name.startswith("ffmpeg"):
            candidate = entry / "bin" / "ffmpeg.exe"
            if candidate.exists():
                return str(candidate)
    found = shutil.which("ffmpeg")
    return found


def _js_runtime_args() -> list[str]:
    """Return extra args to pin a JS runtime if node is available."""
    if shutil.which("node"):
        return ["--js-runtimes", "node"]
    return []


YT_DLP = _find_yt_dlp()
FFMPEG = _find_ffmpeg()
JS_ARGS = _js_runtime_args()

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

# In-memory store for active download progress keyed by download id
_active_downloads: dict[str, dict] = {}


def fetch_info(url: str) -> dict:
    """
    Fetch video metadata via ``yt-dlp --dump-json``.

    Returns a dict with keys:
        id, title, thumbnail, duration, duration_string, channel, url,
        formats (list of video format dicts), subtitles (list of language codes).
    """
    cmd = [YT_DLP] + JS_ARGS + ["--dump-json", "--no-warnings", "--no-playlist", url]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="ignore")

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "yt-dlp returned an error")

    data = json.loads(proc.stdout)

    # Parse video formats ------------------------------------------------
    seen = set()
    formats = []
    for f in data.get("formats", []):
        vcodec = f.get("vcodec")
        if not vcodec or vcodec == "none":
            continue
        height = f.get("height")
        if not height:
            continue

        ext = f.get("ext", "")
        fps = f.get("fps") or 0
        key = (height, ext, fps)
        if key in seen:
            continue
        seen.add(key)

        vcodec_short = vcodec.split(".")[0] if vcodec else "unknown"
        fps_label = f"@{fps}fps" if fps and fps > 30 else ""

        formats.append({
            "formatId": f.get("format_id"),
            "height": height,
            "fps": fps,
            "ext": ext,
            "vcodec": vcodec_short,
            "display": f"{height}p{fps_label} ({ext}) — {vcodec_short}",
        })

    formats.sort(key=lambda x: (x["height"], x["fps"]), reverse=True)

    # Parse available subtitles ------------------------------------------
    subs_raw = data.get("subtitles", {})
    auto_subs_raw = data.get("automatic_captions", {})
    subtitle_langs = []
    seen_langs = set()

    for lang in subs_raw:
        if lang not in seen_langs:
            subtitle_langs.append({"code": lang, "auto": False})
            seen_langs.add(lang)

    for lang in auto_subs_raw:
        if lang not in seen_langs:
            subtitle_langs.append({"code": lang, "auto": True})
            seen_langs.add(lang)

    return {
        "id": data.get("id"),
        "title": data.get("title", "Unknown"),
        "thumbnail": data.get("thumbnail"),
        "duration": data.get("duration"),
        "durationString": data.get("duration_string", "?"),
        "channel": data.get("uploader", "Unknown"),
        "url": url,
        "formats": formats,
        "subtitles": subtitle_langs,
    }


def start_download(
    url: str,
    format_id: str | None = None,
    mode: str = "video",
    subtitle_langs: list[str] | None = None,
    merge_format: str | None = None,
) -> str:
    """
    Begin a download in a background thread.

    Returns a download *id* that can be used to poll progress via ``get_progress()``.
    """
    download_id = uuid.uuid4().hex[:12]
    DATA_DIR.mkdir(exist_ok=True)

    _active_downloads[download_id] = {
        "status": "starting",
        "progress": 0,
        "speed": "",
        "eta": "",
        "filename": "",
        "error": None,
    }

    thread = Thread(
        target=_run_download,
        args=(download_id, url, format_id, mode, subtitle_langs),
        kwargs={"merge_format": merge_format},
        daemon=True,
    )
    thread.start()
    return download_id


def get_progress(download_id: str) -> dict | None:
    """Return the current progress dict for *download_id*, or ``None``."""
    return _active_downloads.get(download_id)


# ---------------------------------------------------------------------------
# Internal download runner
# ---------------------------------------------------------------------------

# Regex to parse yt-dlp progress lines such as:
# [download]  45.2% of  120.50MiB at  5.23MiB/s ETA 00:12
_PROGRESS_RE = re.compile(
    r"\[download\]\s+(?P<pct>[\d.]+)%\s+of\s+\S+\s+at\s+(?P<speed>\S+)\s+ETA\s+(?P<eta>\S+)"
)
# Destination line: [download] Destination: <filename>
_DEST_RE = re.compile(r"\[download\] Destination:\s+(.+)")
# Merge line: [Merger] Merging formats into "<filename>"
_MERGE_RE = re.compile(r'\[Merger\] Merging formats into "(.+)"')
# Already downloaded
_ALREADY_RE = re.compile(r"\[download\]\s+(.+) has already been downloaded")


def _run_download(
    download_id: str,
    url: str,
    format_id: str | None,
    mode: str,
    subtitle_langs: list[str] | None,
    merge_format: str | None = None,
) -> None:
    """Execute yt-dlp and stream progress updates into ``_active_downloads``."""
    state = _active_downloads[download_id]
    state["status"] = "downloading"

    cmd = [YT_DLP] + JS_ARGS + ["--newline", "--no-part", "-P", str(DATA_DIR), "--no-playlist", "--ignore-errors"]

    if FFMPEG:
        cmd.extend(["--ffmpeg-location", FFMPEG])

    if mode == "audio":
        cmd.extend(["-x", "--audio-format", "mp3", "--audio-quality", "0"])
    else:
        if format_id:
            cmd.extend(["-f", f"{format_id}+bestaudio/best"])
            if merge_format:
                cmd.extend(["--merge-output-format", merge_format])
        else:
            cmd.extend(["-f", "bv*+ba/b"])

    # Subtitles
    if subtitle_langs:
        lang_str = ",".join(subtitle_langs)
        cmd.extend([
            "--write-sub",          # manual/uploaded subs
            "--write-auto-sub",     # auto-generated captions
            "--sub-lang", lang_str,
            "--convert-subs", "srt",
        ])

    cmd.append(url)

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="ignore",
        )

        output_lines = []
        for line in proc.stdout:  # type: ignore[union-attr]
            line_stripped = line.strip()
            if not line_stripped:
                continue
            output_lines.append(line_stripped)

            m = _PROGRESS_RE.search(line_stripped)
            if m:
                state["progress"] = float(m.group("pct"))
                state["speed"] = m.group("speed")
                state["eta"] = m.group("eta")
                continue

            m = _DEST_RE.search(line_stripped)
            if m:
                state["filename"] = os.path.basename(m.group(1))
                continue

            m = _MERGE_RE.search(line_stripped)
            if m:
                state["filename"] = os.path.basename(m.group(1))
                state["status"] = "merging"
                continue

            m = _ALREADY_RE.search(line_stripped)
            if m:
                state["filename"] = os.path.basename(m.group(1))
                state["progress"] = 100
                continue

        proc.wait()

        if proc.returncode == 0:
            state["status"] = "completed"
            state["progress"] = 100
        else:
            state["status"] = "failed"
            error_details = "\n".join(output_lines[-10:])  # last 10 lines of output
            state["error"] = f"yt-dlp exited with code {proc.returncode}. Output:\n{error_details}"
            print(f"Download failed with output:\n" + "\n".join(output_lines))

    except Exception as exc:
        state["status"] = "failed"
        state["error"] = str(exc)
