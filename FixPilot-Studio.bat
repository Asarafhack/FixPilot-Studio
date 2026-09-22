@echo off
setlocal
cd /d "%~dp0"

if exist "FixPilot-Studio.exe" (
    start "" "FixPilot-Studio.exe"
    exit /b 0
)

where python >nul 2>nul
if errorlevel 1 (
    echo FixPilot-Studio.exe is not present and Python was not found.
    pause
    exit /b 1
)

python -m app.main
