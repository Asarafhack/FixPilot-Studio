from pathlib import Path

IGNORED_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build"}
EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".json", ".toml", ".txt", ".md", ".yml", ".yaml"}

def scan_project(project_root="."):
    root = Path(project_root).resolve()
    files = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in EXTENSIONS:
            continue
        try:
            if path.stat().st_size > 200_000:
                continue
            files.append(str(path.relative_to(root)))
        except OSError:
            continue

    manifests = {}
    for name in ("package.json", "requirements.txt", "pyproject.toml"):
        p = root / name
        if p.exists():
            try:
                manifests[name] = p.read_text(encoding="utf-8")[:12000]
            except OSError:
                manifests[name] = ""

    return {
        "root": str(root),
        "file_count": len(files),
        "files": files[:500],
        "manifests": manifests,
    }

def project_summary(context):
    lines = [
        f"Project root: {context['root']}",
        f"Relevant files discovered: {context['file_count']}",
    ]
    if context["manifests"]:
        lines.append("Project manifests:")
        for name, content in context["manifests"].items():
            lines.append(f"--- {name} ---")
            lines.append(content[:4000])
    return "\n".join(lines)
