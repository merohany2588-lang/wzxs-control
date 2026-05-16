@echo off
chcp 65001 >nul
title Ultimate C Drive Strike ASCII Safe
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0ultimate_c_drive_strike_ascii_safe.ps1"
pause
