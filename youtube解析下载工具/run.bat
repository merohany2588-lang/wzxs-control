@echo off
chcp 65001 >nul
cd /d %~dp0

if not exist .venv (
  echo [1/4] Creating virtual environment...
  py -3 -m venv .venv
)

call .venv\Scripts\activate.bat

if not exist .deps_ok (
  echo [2/4] First run: installing dependencies...
  python -m pip install -U pip
  python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
  )
  echo ok> .deps_ok
) else (
  echo [2/4] Dependencies already installed. Skipping pip install.
)

echo [3/4] Checking yt-dlp version...
python -c "import yt_dlp; print('yt-dlp', yt_dlp.version.__version__)" 2>nul

echo [4/4] Starting Multi Site Downloader Pro v3.8...
python youtube_downloader_v3_pro.py
pause
