from app.repair.service import repair_and_verify


def test_real_pip_repair_and_verification(tmp_path):
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

    assert result["execution_results"]
    assert result["verification"]["success"] is True

def test_existing_package_install_is_skipped(tmp_path):
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

    install_result = result["execution_results"][0]

    assert install_result["skipped"] is True
    assert install_result["package"] == "flask"