@echo off
chcp 65001
cd /d "%~dp0"

echo.
echo ============================================================
echo Novel Translator - Install Dependencies SAFE
echo ============================================================
echo.

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
)

call ".venv\Scripts\activate.bat"

python -m pip install -U pip
python -m pip install -r requirements.txt

echo.
echo Done.
pause
