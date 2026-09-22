from pathlib import Path
from app.runtime import data_root

def logs_dir():
    path = data_root() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path

def snapshots_dir():
    path = logs_dir() / "snapshots"
    path.mkdir(parents=True, exist_ok=True)
    return path
