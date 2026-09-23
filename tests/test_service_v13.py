from app.repair.service import repair_and_verify


def test_repair_and_verify_empty_plan(tmp_path):
    result = repair_and_verify(
        [],
        cwd=tmp_path,
    )

    assert result["success"] is False
    assert result["stage"] == "planning"


def test_repair_and_verify_blocks_unsafe_plan(tmp_path):
    plan = [
        {
            "action": "pip_install",
            "package": "flask && whoami",
            "risk": "LOW",
        }
    ]

    result = repair_and_verify(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is False
    assert result["stage"] == "execution"
    assert result["verification"] is None


def test_repair_and_verify_successful_import(tmp_path):
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
    assert result["verification"]["success"] is True