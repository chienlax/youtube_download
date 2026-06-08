@echo off
title TubeGrab - YouTube Downloader
echo.
echo  ========================================
echo   TubeGrab - YouTube Video Downloader
echo  ========================================
echo.

:: Start Flask backend
echo  [1/2] Starting backend server (Flask)...
cd /d "%~dp0"
start "TubeGrab Backend" cmd /c "cd backend && ..\venv\Scripts\python.exe app.py"

:: Wait for backend to start
timeout /t 2 /nobreak >nul

:: Start Vite frontend
echo  [2/2] Starting frontend (Vite)...
cd /d "%~dp0frontend"
start "TubeGrab Frontend" cmd /c "npm run dev"

echo.
echo  Both servers are starting!
echo  Backend:  http://127.0.0.1:5000
echo  Frontend: http://localhost:5173
echo.
echo  Press any key to stop both servers...
pause >nul

:: Kill both
taskkill /FI "WINDOWTITLE eq TubeGrab Backend" >nul 2>&1
taskkill /FI "WINDOWTITLE eq TubeGrab Frontend" >nul 2>&1
