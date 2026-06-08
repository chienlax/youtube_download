"""
Flask API server for the YouTube downloader.
Exposes REST endpoints for fetching video info, starting downloads,
streaming progress via SSE, and managing download history.
"""

import time
from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from downloader import fetch_info, start_download, get_progress
import history

app = Flask(__name__)
CORS(app)


# ---------------------------------------------------------------------------
# Video info
# ---------------------------------------------------------------------------

@app.route("/api/info")
def api_info():
    """Fetch video metadata, available formats, and subtitle languages."""
    url = request.args.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing 'url' query parameter"}), 400

    try:
        info = fetch_info(url)
        return jsonify(info)
    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ---------------------------------------------------------------------------
# Download
# ---------------------------------------------------------------------------

@app.route("/api/download", methods=["POST"])
def api_download():
    """
    Start a download.

    JSON body:
        url (str): YouTube video URL
        formatId (str|null): specific format id, or null for best
        mode (str): "video" or "audio"
        subtitles (list[str]): language codes to download
        title (str): video title (for history)
        thumbnail (str|null): thumbnail URL (for history)
    """
    body = request.get_json(force=True)
    url = body.get("url", "").strip()
    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    format_id = body.get("formatId")
    mode = body.get("mode", "video")
    subtitle_langs = body.get("subtitles", [])

    download_id = start_download(url, format_id, mode, subtitle_langs)

    # Store metadata for history recording once download completes
    _pending_meta[download_id] = {
        "title": body.get("title", "Unknown"),
        "url": url,
        "mode": mode,
        "thumbnail": body.get("thumbnail"),
    }

    return jsonify({"downloadId": download_id})


# Metadata cache for downloads not yet recorded in history
_pending_meta: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Progress SSE
# ---------------------------------------------------------------------------

@app.route("/api/download/progress/<download_id>")
def api_progress(download_id: str):
    """
    Server-Sent Events stream for download progress.
    Sends JSON events with keys: status, progress, speed, eta, filename.
    Closes when download finishes (completed / failed).
    """

    def generate():
        while True:
            state = get_progress(download_id)
            if state is None:
                yield f"data: {{}}\n\n"
                break

            import json
            yield f"data: {json.dumps(state)}\n\n"

            if state["status"] in ("completed", "failed"):
                # Record in history
                meta = _pending_meta.pop(download_id, {})
                if meta:
                    history.add_entry(
                        title=meta.get("title", "Unknown"),
                        url=meta.get("url", ""),
                        filename=state.get("filename", ""),
                        status=state["status"],
                        mode=meta.get("mode", "video"),
                        thumbnail=meta.get("thumbnail"),
                    )
                break

            time.sleep(0.5)

    return Response(generate(), mimetype="text/event-stream")


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

@app.route("/api/history")
def api_history():
    """Return all download history entries."""
    return jsonify(history.get_all())


@app.route("/api/history/<entry_id>", methods=["DELETE"])
def api_history_delete(entry_id: str):
    """Delete a single history entry."""
    if history.delete_entry(entry_id):
        return jsonify({"ok": True})
    return jsonify({"error": "Not found"}), 404


@app.route("/api/history", methods=["DELETE"])
def api_history_clear():
    """Clear all history."""
    history.clear_all()
    return jsonify({"ok": True})


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
