@echo off
cd /d "%~dp0"

py -m app

if errorlevel 1 (
    echo.
    echo FixPilot failed to start.
    pause
)