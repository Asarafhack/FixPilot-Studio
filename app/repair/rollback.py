import json
from pathlib import Path
from app.repair.storage import snapshots_dir

SNAPSHOT = snapshots_dir() / "latest.json"

def rollback_project_manifests(project_root="."):
    """Restore only manifest files captured by the latest snapshot.

    Package-manager side effects are not reversed automatically. This is
    intentionally conservative: files are restorable; external package state
    requires a package-manager-specific operation.
    """
    root = Path(project_root).resolve()
    if not SNAPSHOT.exists():
        return {"success": False, "message": "No snapshot exists."}

    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    restored = []

    for name, data in snapshot.get("files", {}).items():
        path = root / name
        path.write_text(data["content"], encoding="utf-8")
        restored.append(name)

    return {
        "success": True,
        "message": "Restored manifest snapshots: " + ", ".join(restored)
        if restored else "No manifest files needed restoration.",
        "restored": restored,
    }
