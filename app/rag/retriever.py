from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
KNOWLEDGE = ROOT / "knowledge"

def _tokens(text):
    return set(re.findall(r"[a-z0-9_\-\.]+", text.lower()))

def retrieve(query, category=None, limit=3):
    q = _tokens(query)
    scored = []
    for path in KNOWLEDGE.rglob("*.md"):
        if path.name.lower() == "readme.md":
            continue
        content = path.read_text(encoding="utf-8")
        score = len(q & _tokens(content))
        if category and category.lower() in content.lower():
            score += 3
        if score:
            scored.append((score, path, content))
    scored.sort(key=lambda x: x[0], reverse=True)
    results = []
    for score, path, content in scored[:limit]:
        clean = " ".join(
            line.strip() for line in content.splitlines()
            if line.strip() and not line.startswith("#")
        )
        results.append({
            "title": path.relative_to(ROOT).as_posix(),
            "content": clean[:900],
            "score": score
        })
    if not results:
        results.append({
            "title": "No local knowledge match",
            "content": "No trusted local document matched this error. FixPilot will not invent documentation.",
            "score": 0
        })
    return results
