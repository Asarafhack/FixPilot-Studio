from app.agent.repair_agent import RepairAgent
from app.repair.approval import (
    approve_repair,
    create_approval_request,
)


def test_repair_agent_blocks_modification_without_approval(
    tmp_path,
    monkeypatch,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "import definitely_missing_package\n",
        encoding="utf-8",
    )

    repair_plan = [
        {
            "action": "pip_install",
            "package": "definitely_missing_package",
            "reason": "Install the missing dependency.",
        }
    ]

    monkeypatch.setattr(
        "app.agent.repair_agent.build_reasoned_repair_plan",
        lambda *args, **kwargs: repair_plan,
    )

    result = RepairAgent().analyze_and_repair(
        command=[
            "py",
            "app.py",
        ],
        project_root=str(tmp_path),
        error_text=(
            "ModuleNotFoundError: "
            "No module named definitely_missing_package"
        ),
        approved=False,
    )

    assert result.success is False
    assert result.repair_plan == repair_plan
    assert result.repair_decisions

    assert result.pipeline is not None

    pipeline_message = str(
        result.pipeline.get("message", "")
    ).lower()

    transaction = result.pipeline.get("transaction")

    if transaction is not None:
        transaction_message = str(
            transaction.get("message", "")
        ).lower()

        combined_message = (
            pipeline_message
            + " "
            + transaction_message
        )
    else:
        combined_message = pipeline_message

    assert (
        "approval" in combined_message
        or result.stage == "approval_required"
    )


def test_approval_request_does_not_execute_repair():
    plan = {
        "action": "pip_install",
        "package": "example-package",
        "reason": "Install dependency.",
    }

    request = create_approval_request(plan)

    assert request["required"] is True
    assert request["approved"] is False
    assert request["action"] == "pip_install"
    assert request["package"] == "example-package"


def test_explicit_approval_changes_only_approval_state():
    plan = {
        "action": "pip_install",
        "package": "example-package",
        "reason": "Install dependency.",
    }

    request = create_approval_request(plan)

    approved_request = approve_repair(request)

    assert approved_request["required"] is True
    assert approved_request["approved"] is True
    assert approved_request["action"] == "pip_install"
    assert approved_request["package"] == "example-package"