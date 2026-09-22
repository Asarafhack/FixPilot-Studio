from pathlib import Path
import sys

from app.context.environment import detect_environment
from app.context.interpreter import inspect_interpreter
from app.context.dependencies import (
    import_to_package,
    parse_requirements,
    analyze_package,
)


def test_environment_detects_python():
    result = detect_environment(".")

    assert result["python"]["available"] is True
    assert result["python"]["version"]
    assert result["python"]["executable"]


def test_interpreter_detection():
    result = inspect_interpreter()

    assert result["executable"]
    assert result["version"]
    assert Path(result["executable"]).exists()


def test_import_package_mapping():
    assert import_to_package("cv2") == "opencv-python"
    assert import_to_package("PIL.Image") == "Pillow"
    assert import_to_package("flask") == "flask"


def test_requirements_parser(tmp_path):
    requirements = tmp_path / "requirements.txt"

    requirements.write_text(
        """
        Flask==3.0.0
        requests>=2.0
        # comment
        """,
        encoding="utf-8",
    )

    result = parse_requirements(requirements)

    names = [item["name"] for item in result]

    assert "Flask" in names
    assert "requests" in names


def test_analyze_installed_package():
    result = analyze_package("flask", ".")

    assert result["package"] == "flask"
    assert result["installed"]["installed"] is True