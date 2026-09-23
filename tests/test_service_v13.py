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
        approved=True,
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

def test_repair_requires_approval_before_pip_install(tmp_path):
    plan = [
        {
            "action": "pip_install",
            "package": "flask",
            "risk": "LOW",
        }
    ]

    result = repair_and_verify(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is False
    assert result["stage"] == "approval_required"
    assert result["approval_request"]["required"] is True
    assert result["approval_request"]["approved"] is False


def test_approved_repair_can_execute(tmp_path):
    plan = [
        {
            "action": "pip_install",
            "package": "flask",
            "risk": "LOW",
        },
        {
            "action": "verify_import",
            "package": "flask",
            "risk": "LOW",
        },
    ]

    result = repair_and_verify(
        plan,
        cwd=tmp_path,
        approved=True,
    )

    assert result["success"] is True
    assert result["stage"] == "completed"


def test_verification_does_not_require_approval(tmp_path):
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