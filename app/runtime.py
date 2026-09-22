from pathlib import Path
import os
import sys

APP_NAME = "FixPilot Studio"
VERSION = "1.0.0"

def app_root():
    # PyInstaller one-file/one-folder builds expose bundled resources via _MEIPASS.
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parents[1]

def data_root():
    # Keep mutable logs/config outside the bundled application.
    base = os.getenv("LOCALAPPDATA")
    if base:
        path = Path(base) / "FixPilotStudio"
    else:
        path = Path.home() / ".fixpilot"
    path.mkdir(parents=True, exist_ok=True)
    return path

def version_text():
    return f"{APP_NAME} v{VERSION}"
