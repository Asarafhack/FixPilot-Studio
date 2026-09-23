
from app.agent.repair_agent import RepairAgent


def test_real_repair_agent_end_to_end_planning(
    tmp_path,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "import definitely_missing_package\n",
        encoding="utf-8",
    )

    result = RepairAgent().analyze_and_repair(
        command=[
            "py",
            "app.py",
        ],
        project_root=str(tmp_path),
        approved=False,
    )

    assert result.success is False

    assert result.reproduction is not None
    assert result.reproduction["success"] is False

    assert result.diagnosis is not None
    assert result.fingerprint is not None
    assert result.root_cause is not None

    assert result.repair_plan
    assert result.pipeline is not None


def test_real_repair_agent_preserves_original_command(
    tmp_path,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "import definitely_missing_package\n",
        encoding="utf-8",
    )

    original_command = [
        "py",
        "app.py",
    ]

    result = RepairAgent().analyze_and_repair(
        command=original_command,
        project_root=str(tmp_path),
        approved=False,
    )

    assert result.command == original_command

    assert result.reproduction is not None

    assert (
        result.reproduction["command"]
        == original_command
    )

    if result.pipeline is not None:
        pipeline_reproduction = result.pipeline.get(
            "reproduction"
        )

        if pipeline_reproduction is not None:
            assert (
                pipeline_reproduction["command"]
                == original_command
            )


def test_real_repair_agent_unknown_failure_has_no_unsafe_plan(
    tmp_path,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "raise RuntimeError('completely unknown failure')\n",
        encoding="utf-8",
    )

    result = RepairAgent().analyze_and_repair(
        command=[
            "py",
            "app.py",
        ],
        project_root=str(tmp_path),
        approved=False,
    )

    assert result.success is False

    assert result.reproduction is not None
    assert result.reproduction["success"] is False

    assert result.repair_plan == []

    assert result.repair_decisions == []

    assert result.stage == "no_repair_plan"


def test_real_repair_agent_returns_repair_decision(
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
            "package": "flask",
            "reason": (
                "Install the missing Flask dependency."
            ),
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
            "No module named flask"
        ),
        approved=False,
    )

    assert result.success is False

    assert result.reproduction is not None
    assert result.reproduction["success"] is False

    assert result.diagnosis is not None
    assert result.fingerprint is not None
    assert result.root_cause is not None

    assert result.repair_plan == repair_plan

    assert result.repair_decisions

    install_decisions = [
        decision
        for decision in result.repair_decisions
        if decision["action"] == "pip_install"
    ]

    assert len(install_decisions) == 1

    decision = install_decisions[0]

    assert decision["target"] == "flask"

    assert decision["requires_approval"] is True

    assert decision["risk_level"] == "low"

    assert decision["reason"]

    assert decision["evidence"]

    assert decision["verification_method"]

    assert decision["confidence"] is not None
