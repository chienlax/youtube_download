# TubeGrab — YouTube Downloader (local)

This repository contains a simple YouTube downloader with a Python/Flask backend (yt-dlp wrapper) and a Vite + React frontend.

This README describes how to set up and run both backend and frontend on Windows. It also explains bundled binary detection and common troubleshooting steps.

## Repository layout

- `backend/` — Flask API and downloader logic
- `frontend/` — Vite + React UI
- `yt-dlp.exe` — optional bundled yt-dlp executable (project root)
- `venv/` — recommended Python virtual environment (not committed)

## Prerequisites

- Windows 10/11 (tested)
- Python 3.10+ (3.12 recommended)
- Node.js (v16+ recommended; Node v24 works)
- npm
- Optional but recommended: `ffmpeg` on PATH or a local `ffmpeg-*/bin/ffmpeg.exe` folder in the project root

If you plan to use the GUI `gui.py`, you'll need a Python environment with `tkinter` available (usually included with standard Windows Python installs).

## Backend setup (Flask + yt-dlp)

1. Open PowerShell and cd to the project root:

```powershell
cd 'C:\Users\ORLab\main_source\youtube_download'
```

2. Create and activate a Python virtual environment (recommended):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Upgrade packaging tools and install dependencies:

```powershell
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r .\backend\requirements.txt
```

4. Optional: place `yt-dlp.exe` in the project root (already included for convenience). Ensure `ffmpeg` is available either on PATH or as a local directory named like `ffmpeg-<version>` containing `bin\ffmpeg.exe`.

5. Start the Flask backend (development server):

```powershell
.\venv\Scripts\python.exe backend\app.py
```

The backend will run on `http://127.0.0.1:5000` by default.

## Frontend setup (Vite + React)

1. From the project root, change into the frontend folder:

```powershell
cd frontend
```

2. Install Node dependencies:

```powershell
npm install
```

3. Start the dev server:

```powershell
npm run dev
```

Vite serves the frontend on `http://localhost:5173` by default. The frontend expects the backend API at `http://127.0.0.1:5000`.

## One-step launcher

`start.bat` in the project root will attempt to start the backend (using `venv\Scripts\python.exe`) and the frontend. Edit it if your venv path differs.

## Running the standalone GUI

If you prefer a local desktop GUI, run:

```powershell
python gui.py
```

The GUI detects `yt-dlp` and `ffmpeg` on PATH or as local files. Use the Browse buttons to point to binaries if auto-detection fails.

## Bundled binaries & detection

- `backend/downloader.py` and `gui.py` look for `yt-dlp.exe` in the project root first, then fall back to the system `yt-dlp`/`yt-dlp.exe` on PATH.
- `ffmpeg` detection prefers a local `ffmpeg-*/bin/ffmpeg.exe` folder, otherwise it uses whatever is on PATH.

## Common issues & troubleshooting

- If `yt-dlp` is not found: ensure `yt-dlp.exe` is in the project root or install `yt-dlp` globally (or add it to PATH).
- If downloads fail with merging errors: ensure `ffmpeg` is available and accessible.
- If the frontend cannot reach the backend: confirm both servers are running and that CORS is enabled (the backend enables CORS by default).

## Useful commands summary

From project root (PowerShell):

```powershell
# Create venv and install backend deps
python -m venv venv
.\venv\Scripts\python.exe -m pip install --upgrade pip
.\venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt

# Start backend
.\venv\Scripts\python.exe backend\app.py

# Frontend (in a separate shell)
cd frontend
npm install
npm run dev

# Or use launcher
start.bat
```

## Contributing

If you add packaging, CI, or distribution, please update this README with platform-specific notes.

---

If you want, I can also:

- add a short `README` section describing the API endpoints
- create a `requirements-dev.txt` or `Makefile`/PowerShell script to automate the setup
- update `start.bat` to auto-create a venv if missing
