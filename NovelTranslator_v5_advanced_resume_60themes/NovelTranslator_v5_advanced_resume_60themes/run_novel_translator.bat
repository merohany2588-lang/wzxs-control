@echo off
chcp 65001
cd /d "%~dp0"

echo.
echo ============================================================
echo Novel Translator - SAFE LAUNCHER
echo ============================================================
echo Current folder:
cd
echo.

if not exist logs mkdir logs

set "PYEXE="

echo [1/5] Checking Python launcher py -3...
py -3 --version
if not errorlevel 1 (
    set "PYEXE=py -3"
)

if "%PYEXE%"=="" (
    echo [1/5] py -3 not available, checking python...
    python --version
    if not errorlevel 1 (
        set "PYEXE=python"
    )
)

if "%PYEXE%"=="" (
    echo.
    echo [ERROR] Python not found.
    echo Install Python 3.10/3.11/3.12 and enable Add Python to PATH.
    echo.
    pause
    exit /b 1
)

echo [OK] Python command: %PYEXE%
echo.

echo [2/5] Checking virtual environment...
if not exist ".venv\Scripts\python.exe" (
    echo Creating .venv ...
    %PYEXE% -m venv .venv
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to create .venv
        pause
        exit /b 1
    )
)

echo [3/5] Activating .venv...
call ".venv\Scripts\activate.bat"
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to activate .venv
    pause
    exit /b 1
)

echo [4/5] Installing/checking dependencies...
python -c "import PySide6"
if errorlevel 1 (
    echo Installing dependencies from requirements.txt ...
    python -m pip install -U pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo [ERROR] pip install failed.
        echo Try running install_deps_safe.bat
        pause
        exit /b 1
    )
)

echo.
echo [5/5] Starting app...
python main.py

if errorlevel 1 (
    echo.
    echo [ERROR] App crashed or failed to start.
    echo Run run_debug_safe.bat to see details.
    pause
    exit /b 1
)

echo.
echo App closed.
pause
