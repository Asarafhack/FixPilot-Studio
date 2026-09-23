from pathlib import Path

from app.repair.transaction import RepairTransaction


def test_transaction_verifies_original_command_after_repair(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    original_command = [
        "py",
        "-c",
        "print('original command works')",
    ]

    plan = [
        {
            "action": "verify_environment",
            "reason": "test verification",
        }
    ]

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        lambda *args, **kwargs: {
            "success": True,
            "stage": "completed",
            "message": "repair complete",
            "execution_results": [],
            "verification": {},
        },
    )

    result = RepairTransaction().execute(
        plan=plan,
        project_root=str(project),
        original_command=original_command,
        approved=True,
    )

    assert result.completed is True
    assert result.status == "completed"
    assert result.original_command_verification is not None
    assert (
        result.original_command_verification["success"]
        is True
    )
    assert (
        result.original_command_verification[
            "failure_resolved"
        ]
        is True
    )


def test_transaction_fails_when_original_command_still_fails(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    original_command = [
        "py",
        "-c",
        "raise SystemExit(1)",
    ]

    plan = [
        {
            "action": "verify_environment",
            "reason": "test verification",
        }
    ]

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        lambda *args, **kwargs: {
            "success": True,
            "stage": "completed",
            "message": "repair complete",
            "execution_results": [],
            "verification": {},
        },
    )

    result = RepairTransaction().execute(
        plan=plan,
        project_root=str(project),
        original_command=original_command,
        approved=True,
    )

    assert result.completed is False
    assert result.status == "verification_failed"
    assert (
        result.original_command_verification[
            "failure_resolved"
        ]
        is False
    )


def test_transaction_without_original_command_can_complete(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    plan = [
        {
            "action": "verify_environment",
            "reason": "test verification",
        }
    ]

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        lambda *args, **kwargs: {
            "success": True,
            "stage": "completed",
            "message": "repair complete",
            "execution_results": [],
            "verification": {},
        },
    )

    result = RepairTransaction().execute(
        plan=plan,
        project_root=str(project),
        original_command=None,
        approved=True,
    )

    assert result.completed is True
    assert result.status == "completed"
    assert result.original_command_verification is None


def test_transaction_preserves_snapshot_change_state(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    test_file = project / "test.txt"
    test_file.write_text(
        "before",
        encoding="utf-8",
    )

    plan = [
        {
            "action": "verify_environment",
            "reason": "test verification",
        }
    ]

    def fake_repair(*args, **kwargs):
        test_file.write_text(
            "after",
            encoding="utf-8",
        )

        return {
            "success": True,
            "stage": "completed",
            "message": "repair complete",
            "execution_results": [],
            "verification": {},
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    result = RepairTransaction().execute(
        plan=plan,
        project_root=str(project),
        approved=True,
    )

    assert result.completed is True
    assert result.changed is True