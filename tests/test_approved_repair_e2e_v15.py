from app.repair.approval import (
    approve_repair,
    create_approval_request,
)
from app.repair.executor import execute_plan


def test_approved_pip_repair_reaches_executor(
    tmp_path,
    monkeypatch,
):
    executed_commands = []

    def fake_run(command, cwd=None):
        executed_commands.append(
            {
                "command": command,
                "cwd": cwd,
            }
        )

        return True, "Simulated package installation succeeded."

    monkeypatch.setattr(
        "app.repair.executor._run",
        fake_run,
    )

    plan = {
        "action": "pip_install",
        "package": "example-package",
        "reason": "Install the missing dependency.",
    }

    approval_request = create_approval_request(plan)

    assert approval_request["required"] is True
    assert approval_request["approved"] is False

    approved_request = approve_repair(
        approval_request
    )

    assert approved_request["approved"] is True

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is True
    assert result["blocked"] is False
    assert result["action"] == "pip_install"
    assert result["package"] == "example-package"

    assert len(executed_commands) == 1

    command = executed_commands[0]["command"]

    assert command[0] != "pip"
    assert command[1] == "-m"
    assert command[2] == "pip"
    assert command[3] == "install"
    assert command[4] == "example-package"


def test_unapproved_request_never_executes():
    plan = {
        "action": "pip_install",
        "package": "example-package",
        "reason": "Install the missing dependency.",
    }

    approval_request = create_approval_request(plan)

    assert approval_request["required"] is True
    assert approval_request["approved"] is False

    # The approval layer itself does not execute anything.
    assert approval_request["approved"] is False


def test_non_modifying_action_does_not_require_approval(
    tmp_path,
):
    plan = {
        "action": "verify_import",
        "package": "sys",
    }

    approval_request = create_approval_request(plan)

    assert approval_request["required"] is False
    assert approval_request["approved"] is True

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is True
    assert result["blocked"] is False
    assert result["action"] == "verify_import"