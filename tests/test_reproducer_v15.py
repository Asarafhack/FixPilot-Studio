from pathlib import Path

import pytest

from app.diagnostics.reproducer import (
    FailureReproducer,
    reproduce_failure,
)


def test_reproducer_captures_success(tmp_path):
    reproducer = FailureReproducer()

    result = reproducer.reproduce(
        ["cmd", "/c", "echo", "hello"],
        tmp_path,
    )

    assert result.success is True
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.timed_out is False
    assert result.duration_seconds >= 0


def test_reproducer_captures_failure(tmp_path):
    reproducer = FailureReproducer()

    result = reproducer.reproduce(
        ["cmd", "/c", "exit", "7"],
        tmp_path,
    )

    assert result.success is False
    assert result.exit_code == 7
    assert result.timed_out is False


def test_reproducer_captures_stderr(tmp_path):
    reproducer = FailureReproducer()

    result = reproducer.reproduce(
        [
            "cmd",
            "/c",
            "echo",
            "failure-message",
            "1>&2",
        ],
        tmp_path,
    )

    assert result.success is True
    assert "failure-message" in result.stderr
    assert "failure-message" in result.combined_output


def test_reproducer_uses_project_root(tmp_path):
    marker = tmp_path / "marker.txt"
    marker.write_text("FixPilot", encoding="utf-8")

    reproducer = FailureReproducer()

    result = reproducer.reproduce(
        [
            "cmd",
            "/c",
            "type",
            "marker.txt",
        ],
        tmp_path,
    )

    assert result.success is True
    assert "FixPilot" in result.stdout


def test_reproducer_rejects_shell_string(tmp_path):
    reproducer = FailureReproducer()

    with pytest.raises(TypeError):
        reproducer.reproduce(
            "cmd /c echo unsafe",
            tmp_path,
        )


def test_reproducer_rejects_empty_command(tmp_path):
    reproducer = FailureReproducer()

    with pytest.raises(ValueError):
        reproducer.reproduce([], tmp_path)


def test_reproducer_rejects_missing_project_root(tmp_path):
    reproducer = FailureReproducer()

    missing = tmp_path / "does-not-exist"

    with pytest.raises(FileNotFoundError):
        reproducer.reproduce(
            ["cmd", "/c", "echo", "test"],
            missing,
        )


def test_reproducer_timeout(tmp_path):
    reproducer = FailureReproducer(timeout=1)

    result = reproducer.reproduce(
        [
            "cmd",
            "/c",
            "ping",
            "127.0.0.1",
            "-n",
            "10",
        ],
        tmp_path,
        timeout=1,
    )

    assert result.success is False
    assert result.timed_out is True
    assert result.exit_code is None


def test_reproducer_returns_dict(tmp_path):
    result = reproduce_failure(
        ["cmd", "/c", "echo", "FixPilot"],
        tmp_path,
    )

    assert isinstance(result, dict)
    assert result["success"] is True
    assert "FixPilot" in result["stdout"]
    assert result["project_root"] == str(Path(tmp_path).resolve())