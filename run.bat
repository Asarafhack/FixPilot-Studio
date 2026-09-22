@echo off
setlocal
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found.
    pause
    exit /b 1
)
python -m app.main
pause
