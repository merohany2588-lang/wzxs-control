@echo off
chcp 65001 >nul
cd /d %~dp0
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -U "yt-dlp[default]"
python -m yt_dlp --version
echo.
echo yt-dlp updated in current virtual environment.
pause
