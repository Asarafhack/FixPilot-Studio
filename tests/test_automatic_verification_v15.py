from app.repair.verifier import verify_plan


def test_verification_passes_when_original_command_succeeds(
    tmp_path,
    monkeypatch,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "print('repair successful')\n",
        encoding="utf-8",
    )

    plan = [
        {
            "action": "verify_environment",
        }
    ]

    def fake_original_command(command, cwd=None):
        return {
            "returncode": 0,
            "output": "repair successful",
        }

    monkeypatch.setattr(
        "app.repair.verifier._run_original_command",
        fake_original_command,
    )

    result = verify_plan(
        plan,
        results=[],
        cwd=tmp_path,
        original_command=[
            "py",
            "app.py",
        ],
    )

    assert result["success"] is True
    assert result["message"] == (
        "Repair verification passed."
    )
    assert result["command_result"]["returncode"] == 0
    assert result["verification_results"]


def test_verification_fails_when_original_command_still_fails(
    tmp_path,
    monkeypatch,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "raise RuntimeError('still broken')\n",
        encoding="utf-8",
    )

    plan = [
        {
            "action": "verify_environment",
        }
    ]

    def fake_original_command(command, cwd=None):
        return {
            "returncode": 1,
            "output": "still broken",
        }

    monkeypatch.setattr(
        "app.repair.verifier._run_original_command",
        fake_original_command,
    )

    result = verify_plan(
        plan,
        results=[],
        cwd=tmp_path,
        original_command=[
            "py",
            "app.py",
        ],
    )

    assert result["success"] is False
    assert result["command_result"]["returncode"] == 1

    assert any(
        "Original command still exits" in item
        for item in result["message"].splitlines()
    )


def test_verification_uses_exact_original_command(
    tmp_path,
    monkeypatch,
):
    captured = {}

    plan = [
        {
            "action": "verify_environment",
        }
    ]

    original_command = [
        "py",
        "app.py",
        "--mode",
        "production",
    ]

    def fake_original_command(command, cwd=None):
        captured["command"] = command
        captured["cwd"] = cwd

        return {
            "returncode": 0,
            "output": "ok",
        }

    monkeypatch.setattr(
        "app.repair.verifier._run_original_command",
        fake_original_command,
    )

    result = verify_plan(
        plan,
        results=[],
        cwd=tmp_path,
        original_command=original_command,
    )

    assert result["success"] is True
    assert captured["command"] == original_command
    assert captured["cwd"] == tmp_path


def test_verification_detects_failed_python_import(
    tmp_path,
):
    plan = [
        {
            "action": "pip_install",
            "package": "definitely_missing_package",
        }
    ]

    result = verify_plan(
        plan,
        results=[],
        cwd=tmp_path,
        original_command=None,
    )

    assert result["success"] is False
    assert result["verification_results"]

    verification = result["verification_results"][0]

    assert verification["success"] is False
    assert (
        "definitely_missing_package"
        in verification["message"]
    )