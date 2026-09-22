import tempfile
from pathlib import Path
from app.context.scanner import scan_project
from app.agent.project_reasoner import reason_about_project

def test_project_context_reads_manifest():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "package.json").write_text(
            '{"dependencies":{"express":"^5.0.0"}}', encoding="utf-8"
        )
        (root / "app.js").write_text("require('express')", encoding="utf-8")
        result = scan_project(root)
        assert "package.json" in result["manifests"]
        assert result["file_count"] == 2

def test_project_reasoner_uses_context():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "requirements.txt").write_text("flask==3.0.0\n", encoding="utf-8")
        result = reason_about_project(
            "ModuleNotFoundError: No module named flask", root
        )
        assert result["project_hints"]
