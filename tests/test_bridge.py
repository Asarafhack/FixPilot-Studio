import json
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

# Structural test: the bridge module should import without third-party dependencies.
def test_bridge_import():
    from app.bridge.server import Handler, HOST, PORT
    assert HOST == "127.0.0.1"
    assert PORT == 8765
    assert Handler is not None

def test_extension_files_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "ide" / "vscode-fixpilot" / "package.json").exists()
    assert (root / "ide" / "vscode-fixpilot" / "extension.js").exists()
