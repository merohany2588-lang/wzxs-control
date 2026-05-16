@echo off
chcp 65001 >nul
cd /d %~dp0
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
if not exist .deps_ok (
  echo Installing dependencies first time only...
  python -m pip install -U pip
  python -m pip install -r requirements.txt
  if errorlevel 1 pause & exit /b 1
  echo ok> .deps_ok
) else (
  echo Dependencies already installed. Skipping pip install.
)
set ICON_ARG=
if exist app.ico set ICON_ARG=--icon=app.ico
if not exist app.ico echo [WARN] app.ico not found. EXE will be built without custom icon.
pyinstaller --noconfirm --clean --onefile --windowed %ICON_ARG% --name YouTubeDownloaderPro youtube_downloader_v3_pro.py
echo.
echo Build finished. EXE path: dist\YouTubeDownloaderPro.exe
pause
