$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

Write-Host ""
Write-Host "============================================================"
Write-Host "Novel Translator - PowerShell Launcher"
Write-Host "============================================================"

if (!(Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

$py = $null
try {
    py -3 --version
    $py = "py -3"
} catch {
    try {
        python --version
        $py = "python"
    } catch {}
}

if (!$py) {
    Write-Host "[ERROR] Python not found."
    Read-Host "Press Enter to exit"
    exit 1
}

if (!(Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "Creating .venv ..."
    Invoke-Expression "$py -m venv .venv"
}

& ".\.venv\Scripts\Activate.ps1"

try {
    python -c "import PySide6"
} catch {
    python -m pip install -U pip
    python -m pip install -r requirements.txt
}

python main.py

Read-Host "Press Enter to exit"
