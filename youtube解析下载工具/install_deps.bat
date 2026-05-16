@echo off
chcp 65001 >nul
cd /d %~dp0
if not exist .venv py -3 -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -U pip
python -m pip install -r requirements.txt
if errorlevel 1 pause & exit /b 1
echo ok> .deps_ok
echo Dependencies installed/updated.
pause
