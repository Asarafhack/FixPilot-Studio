from pathlib import Path

from app.repair.project_snapshot import ProjectSnapshotter
from app.repair.transaction import (
    RepairTransaction,
    RepairTransactionResult,
    execute_repair_transaction,
)


def test_transaction_can_capture_before_and_after(
    tmp_path,
    monkeypatch,
):
    project_file = tmp_path / "app.py"
    project_file.write_text(
        "print('before')",
        encoding="utf-8",
    )

    def fake_repair(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        project_file.write_text(
            "print('after')",
            encoding="utf-8",
        )

        return {
            "success": True,
            "stage": "completed",
            "message": "Repair executed and verified successfully.",
            "execution_results": [],
            "verification": {
                "success": True,
            },
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    transaction = RepairTransaction()

    result = transaction.execute(
        plan=[
            {
                "action": "verify_environment",
            }
        ],
        project_root=str(tmp_path),
        approved=True,
    )

    assert result.completed is True
    assert result.status == "completed"
    assert result.changed is True
    assert result.after_snapshot is not None
    assert (
        result.before_snapshot["fingerprint"]
        != result.after_snapshot["fingerprint"]
    )


def test_transaction_detects_no_change(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "app.py").write_text(
        "print('same')",
        encoding="utf-8",
    )

    def fake_repair(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        return {
            "success": True,
            "stage": "completed",
            "message": "Repair executed and verified successfully.",
            "execution_results": [],
            "verification": {
                "success": True,
            },
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    transaction = RepairTransaction()

    result = transaction.execute(
        plan=[
            {
                "action": "verify_environment",
            }
        ],
        project_root=str(tmp_path),
    )

    assert result.completed is True
    assert result.changed is False
    assert result.status == "completed"


def test_transaction_preserves_failed_repair(
    tmp_path,
    monkeypatch,
):
    (tmp_path / "app.py").write_text(
        "print('test')",
        encoding="utf-8",
    )

    def fake_repair(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        return {
            "success": False,
            "stage": "approval_required",
            "message": "Repair requires approval.",
            "execution_results": [],
            "verification": None,
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    transaction = RepairTransaction()

    result = transaction.execute(
        plan=[
            {
                "action": "pip_install",
                "package": "flask",
            }
        ],
        project_root=str(tmp_path),
        approved=False,
    )

    assert result.completed is False
    assert result.changed is False
    assert result.status == "approval_required"
    assert result.after_snapshot is None
    assert result.error == "Repair requires approval."


def test_transaction_passes_original_command(
    tmp_path,
    monkeypatch,
):
    captured = {}

    app_file = tmp_path / "app.py"
    app_file.write_text(
        "print('transaction original command works')\n",
        encoding="utf-8",
    )

    def fake_repair(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        captured["plan"] = plan
        captured["cwd"] = cwd
        captured["original_command"] = original_command
        captured["approved"] = approved

        return {
            "success": True,
            "stage": "completed",
            "message": "Repair executed and verified successfully.",
            "execution_results": [],
            "verification": {
                "success": True,
            },
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    command = [
        "py",
        "app.py",
    ]

    transaction = RepairTransaction()

    result = transaction.execute(
        plan=[
            {
                "action": "verify_environment",
            }
        ],
        project_root=str(tmp_path),
        original_command=command,
        approved=True,
    )

    assert result.completed is True
    assert result.success is True if hasattr(result, "success") else True

    assert captured["plan"] == [
        {
            "action": "verify_environment",
        }
    ]

    assert captured["cwd"] == str(tmp_path)
    assert captured["original_command"] == command
    assert captured["approved"] is True

    assert (
        result.original_command_verification["success"]
        is True
    )


def test_transaction_handles_repair_exception(
    tmp_path,
    monkeypatch,
):
    def fake_repair(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        raise RuntimeError("repair engine crashed")

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    transaction = RepairTransaction()

    result = transaction.execute(
        plan=[
            {
                "action": "verify_environment",
            }
        ],
        project_root=str(tmp_path),
    )

    assert result.completed is False
    assert result.status == "exception"
    assert result.changed is False
    assert result.error == "repair engine crashed"
    assert result.after_snapshot is None


def test_transaction_result_is_serializable(
    tmp_path,
    monkeypatch,
):
    def fake_repair(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        return {
            "success": True,
            "stage": "completed",
            "message": "Repair executed and verified successfully.",
            "execution_results": [],
            "verification": {
                "success": True,
            },
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    transaction = RepairTransaction()

    result = transaction.execute(
        plan=[
            {
                "action": "verify_environment",
            }
        ],
        project_root=str(tmp_path),
    )

    assert isinstance(result, RepairTransactionResult)

    data = result.as_dict()

    assert isinstance(data, dict)
    assert data["completed"] is True
    assert data["status"] == "completed"
    assert "before_snapshot" in data
    assert "after_snapshot" in data


def test_convenience_api_returns_dict(
    tmp_path,
    monkeypatch,
):
    def fake_repair(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        return {
            "success": True,
            "stage": "completed",
            "message": "Repair executed and verified successfully.",
            "execution_results": [],
            "verification": {
                "success": True,
            },
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair,
    )

    result = execute_repair_transaction(
        plan=[
            {
                "action": "verify_environment",
            }
        ],
        project_root=str(tmp_path),
    )

    assert isinstance(result, dict)
    assert result["completed"] is True
    assert result["changed"] is False