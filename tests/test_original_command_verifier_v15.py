from pathlib import Path

import pytest

from app.diagnostics.original_command_verifier import (
    OriginalCommandVerification,
    OriginalCommandVerifier,
    verify_original_command,
)


def test_original_command_succeeds(tmp_path):
    verifier = OriginalCommandVerifier()

    result = verifier.verify(
        ["cmd", "/c", "echo", "FixPilot"],
        str(tmp_path),
    )

    assert isinstance(result, OriginalCommandVerification)
    assert result.success is True
    assert result.failure_resolved is True
    assert result.exit_code == 0
    assert "FixPilot" in result.output
    assert result.timed_out is False


def test_original_command_failure_is_detected(tmp_path):
    verifier = OriginalCommandVerifier()

    result = verifier.verify(
        ["cmd", "/c", "exit", "5"],
        str(tmp_path),
    )

    assert result.success is False
    assert result.failure_resolved is False
    assert result.exit_code == 5


def test_original_command_preserves_arguments(tmp_path):
    verifier = OriginalCommandVerifier()

    command = [
        "cmd",
        "/c",
        "echo",
        "hello world",
    ]

    result = verifier.verify(
        command,
        str(tmp_path),
    )

    assert result.command == command


def test_original_command_uses_project_root(tmp_path):
    marker = tmp_path / "marker.txt"

    marker.write_text(
        "FixPilot verification",
        encoding="utf-8",
    )

    verifier = OriginalCommandVerifier()

    result = verifier.verify(
        [
            "cmd",
            "/c",
            "type",
            "marker.txt",
        ],
        str(tmp_path),
    )

    assert result.success is True
    assert "FixPilot verification" in result.stdout


def test_original_command_captures_stderr(tmp_path):
    verifier = OriginalCommandVerifier()

    result = verifier.verify(
        [
            "cmd",
            "/c",
            "echo",
            "verification-error",
            "1>&2",
        ],
        str(tmp_path),
    )

    assert result.success is True
    assert "verification-error" in result.stderr
    assert "verification-error" in result.output


def test_original_command_timeout(tmp_path):
    verifier = OriginalCommandVerifier(timeout=1)

    result = verifier.verify(
        [
            "cmd",
            "/c",
            "ping",
            "127.0.0.1",
            "-n",
            "10",
        ],
        str(tmp_path),
        timeout=1,
    )

    assert result.success is False
    assert result.failure_resolved is False
    assert result.timed_out is True
    assert result.exit_code is None


def test_original_command_rejects_shell_string(tmp_path):
    verifier = OriginalCommandVerifier()

    with pytest.raises(TypeError):
        verifier.verify(
            "cmd /c echo unsafe",
            str(tmp_path),
        )


def test_original_command_rejects_missing_root(tmp_path):
    verifier = OriginalCommandVerifier()

    missing = tmp_path / "missing"

    with pytest.raises(FileNotFoundError):
        verifier.verify(
            ["cmd", "/c", "echo", "test"],
            str(missing),
        )


def test_original_command_returns_dict(tmp_path):
    result = verify_original_command(
        ["cmd", "/c", "echo", "FixPilot"],
        str(tmp_path),
    )

    assert isinstance(result, dict)
    assert result["success"] is True
    assert result["failure_resolved"] is True
    assert result["command"] == [
        "cmd",
        "/c",
        "echo",
        "FixPilot",
    ]
    assert result["project_root"] == str(
        Path(tmp_path).resolve()
    )