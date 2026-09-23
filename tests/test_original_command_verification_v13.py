from app.repair.service import repair_and_verify


def test_original_command_verification_passes(tmp_path):
    plan = [
        {
            "action": "verify_import",
            "package": "json",
            "risk": "LOW",
        }
    ]

    result = repair_and_verify(
        plan,
        cwd=tmp_path,
        original_command=[
            "py",
            "-c",
            "import json",
        ],
    )

    assert result["success"] is True
    assert result["stage"] == "completed"

    command_result = result["verification"]["command_result"]

    assert command_result is not None
    assert command_result["returncode"] == 0


def test_original_command_verification_detects_failure(tmp_path):
    plan = [
        {
            "action": "verify_import",
            "package": "json",
            "risk": "LOW",
        }
    ]

    result = repair_and_verify(
        plan,
        cwd=tmp_path,
        original_command=[
            "py",
            "-c",
            "raise SystemExit(1)",
        ],
    )

    assert result["success"] is False
    assert result["stage"] == "verification"

    command_result = result["verification"]["command_result"]

    assert command_result is not None
    assert command_result["returncode"] == 1