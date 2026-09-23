from pathlib import Path

import pytest

from app.diagnostics.command_record import (
    OriginalCommand,
    OriginalCommandCapture,
    capture_original_command,
)


def test_capture_command(tmp_path):
    capture = OriginalCommandCapture()

    record = capture.capture(
        ["python", "app.py"],
        tmp_path,
    )

    assert isinstance(record, OriginalCommand)
    assert record.command == ["python", "app.py"]
    assert record.project_root == str(Path(tmp_path).resolve())
    assert record.source == "user"
    assert record.description == ""


def test_capture_preserves_command_order(tmp_path):
    capture = OriginalCommandCapture()

    record = capture.capture(
        ["npm", "run", "dev", "--", "--host", "127.0.0.1"],
        tmp_path,
    )

    assert record.command == [
        "npm",
        "run",
        "dev",
        "--",
        "--host",
        "127.0.0.1",
    ]


def test_capture_metadata(tmp_path):
    capture = OriginalCommandCapture()

    record = capture.capture(
        ["py", "app.py"],
        tmp_path,
        source="terminal",
        description="Original failing application command",
    )

    assert record.source == "terminal"
    assert record.description == "Original failing application command"


def test_capture_returns_serializable_dict(tmp_path):
    result = capture_original_command(
        ["npm", "start"],
        tmp_path,
        source="vscode",
        description="Start development server",
    )

    assert isinstance(result, dict)
    assert result["command"] == ["npm", "start"]
    assert result["project_root"] == str(Path(tmp_path).resolve())
    assert result["source"] == "vscode"
    assert result["description"] == "Start development server"


def test_rejects_shell_string(tmp_path):
    capture = OriginalCommandCapture()

    with pytest.raises(TypeError):
        capture.capture(
            "python app.py",
            tmp_path,
        )


def test_rejects_empty_command(tmp_path):
    capture = OriginalCommandCapture()

    with pytest.raises(ValueError):
        capture.capture([], tmp_path)


def test_rejects_non_string_argument(tmp_path):
    capture = OriginalCommandCapture()

    with pytest.raises(TypeError):
        capture.capture(
            ["python", 123],
            tmp_path,
        )


def test_rejects_missing_project_root(tmp_path):
    capture = OriginalCommandCapture()

    missing = tmp_path / "missing-project"

    with pytest.raises(FileNotFoundError):
        capture.capture(
            ["python", "app.py"],
            missing,
        )


def test_rejects_empty_source(tmp_path):
    capture = OriginalCommandCapture()

    with pytest.raises(ValueError):
        capture.capture(
            ["python", "app.py"],
            tmp_path,
            source="",
        )


def test_rejects_invalid_description(tmp_path):
    capture = OriginalCommandCapture()

    with pytest.raises(TypeError):
        capture.capture(
            ["python", "app.py"],
            tmp_path,
            description=123,
        )