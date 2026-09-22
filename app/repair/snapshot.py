import hashlib
import json
from pathlib import Path
from app.repair.storage import snapshots_dir

SNAPSHOT_DIR = snapshots_dir()

def _sha256(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def create_project_snapshot(project_root="."):
    root = Path(project_root).resolve()
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    files = {}
    for name in ("requirements.txt", "pyproject.toml", "package.json", "package-lock.json"):
        p = root / name
        if p.exists() and p.is_file():
            files[name] = {
                "sha256": _sha256(p),
                "size": p.stat().st_size,
                "content": p.read_text(encoding="utf-8", errors="replace")[:100000],
            }

    snapshot = {
        "root": str(root),
        "files": files,
    }
    target = SNAPSHOT_DIR / "latest.json"
    target.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    return target

def compare_project_snapshot(project_root="."):
    root = Path(project_root).resolve()
    target = SNAPSHOT_DIR / "latest.json"
    if not target.exists():
        return {"available": False, "changed": []}

    snapshot = json.loads(target.read_text(encoding="utf-8"))
    changed = []
    for name, before in snapshot.get("files", {}).items():
        p = root / name
        if not p.exists():
            changed.append({"file": name, "change": "deleted"})
            continue
        after = _sha256(p)
        if after != before["sha256"]:
            changed.append({"file": name, "change": "modified"})
    for name in ("requirements.txt", "pyproject.toml", "package.json", "package-lock.json"):
        if name not in snapshot.get("files", {}) and (root / name).exists():
            changed.append({"file": name, "change": "created"})
    return {"available": True, "changed": changed}
