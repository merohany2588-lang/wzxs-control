@echo off
chcp 65001
cd /d "%~dp0"

echo.
echo ============================================================
echo Novel Translator - DEBUG SAFE
echo ============================================================
echo.

if not exist logs mkdir logs

set "PYEXE="

py -3 --version
if not errorlevel 1 set "PYEXE=py -3"

if "%PYEXE%"=="" (
    python --version
    if not errorlevel 1 set "PYEXE=python"
)

if "%PYEXE%"=="" (
    echo [ERROR] Python not found.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    %PYEXE% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

python -m pip show PySide6
if errorlevel 1 (
    python -m pip install -U pip
    python -m pip install -r requirements.txt
)

echo.
echo ========== PYTHON VERSION ==========
python --version
echo.
echo ========== START MAIN ==========
python main.py
echo ========== END MAIN ==========
echo.

pause
