from app.repair.service import repair_and_verify


def test_real_automatic_verification(tmp_path):
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
    )

    assert result["success"] is True
    assert result["stage"] == "completed"

    verification = result["verification"]

    assert verification["success"] is True
    assert verification["verification_results"]

    check = verification["verification_results"][0]

    assert check["success"] is True
    assert check["module"] == "json"


def test_real_automatic_verification_detects_failure(tmp_path):
    plan = [
        {
            "action": "verify_import",
            "package": "fixpilot_module_that_does_not_exist_xyz",
            "risk": "LOW",
        }
    ]

    result = repair_and_verify(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is False
    assert result["stage"] == "verification"

    verification = result["verification"]

    assert verification["success"] is False
    assert verification["verification_results"]

    check = verification["verification_results"][0]

    assert check["success"] is False