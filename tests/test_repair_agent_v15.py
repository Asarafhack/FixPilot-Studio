
from app.agent.repair_agent import RepairAgent


def test_repair_agent_detects_already_working_command(
    tmp_path,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "print('works')",
    ]

    result = RepairAgent().analyze_and_repair(
        command=command,
        project_root=str(project),
    )

    assert result.success is True
    assert result.stage == "already_resolved"
    assert result.repair_plan == []
    assert result.repair_decisions == []
    assert result.diagnosis is None
    assert result.root_cause is None


def test_repair_agent_reproduces_failure_and_builds_analysis(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "raise ModuleNotFoundError('No module named missing_package')",
    ]

    fake_plan = [
        {
            "action": "verify_environment",
            "reason": "test repair",
        }
    ]

    monkeypatch.setattr(
        "app.agent.repair_agent.analyze_root_cause",
        lambda *args, **kwargs: {
            "category": "missing_dependency",
            "confidence": 0.95,
            "reason": "The dependency is missing.",
        },
    )

    monkeypatch.setattr(
        "app.agent.repair_agent.build_reasoned_repair_plan",
        lambda *args, **kwargs: fake_plan,
    )

    class FakePipelineResult:
        success = False
        stage = "approval_required"
        message = "Approval required."

        def as_dict(self):
            return {
                "success": False,
                "stage": "approval_required",
                "message": "Approval required.",
            }

    class FakePipeline:
        def __init__(self):
            class FakeReproducer:
                def reproduce(
                    self,
                    command,
                    project_root,
                ):
                    from app.diagnostics.reproducer import (
                        ReproductionResult,
                    )

                    return ReproductionResult(
                        command=list(command),
                        project_root=project_root,
                        success=False,
                        exit_code=1,
                        stdout="",
                        stderr=(
                            "ModuleNotFoundError: "
                            "No module named missing_package"
                        ),
                        combined_output=(
                            "ModuleNotFoundError: "
                            "No module named missing_package"
                        ),
                        timed_out=False,
                        duration_seconds=0.01,
                    )

            self.reproducer = FakeReproducer()

        def run(
            self,
            command,
            project_root,
            plan,
            approved,
        ):
            assert command
            assert project_root
            assert plan == fake_plan
            assert approved is False

            return FakePipelineResult()

    agent = RepairAgent(
        pipeline=FakePipeline(),
    )

    result = agent.analyze_and_repair(
        command=command,
        project_root=str(project),
    )

    assert result.success is False
    assert result.stage == "approval_required"
    assert result.diagnosis is not None
    assert result.fingerprint is not None
    assert result.root_cause is not None
    assert result.repair_plan == fake_plan
    assert result.repair_decisions
    assert result.pipeline is not None


def test_repair_agent_uses_supplied_error_text(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "raise SystemExit(1)",
    ]

    supplied_error = (
        "ModuleNotFoundError: "
        "No module named flask"
    )

    captured = {}

    def fake_diagnose(error):
        captured["diagnosis_error"] = error

        return {
            "category": "missing_dependency",
            "category_code": "missing_dependency",
        }

    monkeypatch.setattr(
        "app.agent.repair_agent.diagnose_error",
        fake_diagnose,
    )

    def fake_root_cause(error, **kwargs):
        captured["root_cause_error"] = error

        return {
            "error_type": "ModuleNotFoundError",
            "message": (
                "ModuleNotFoundError: "
                "No module named flask"
            ),
            "reason": "The Flask dependency is missing.",
            "confidence": 0.95,
        }

    monkeypatch.setattr(
        "app.agent.repair_agent.analyze_root_cause",
        fake_root_cause,
    )

    def fake_plan(error, **kwargs):
        captured["plan_error"] = error

        return [
            {
                "action": "verify_environment",
                "reason": "test",
            }
        ]

    monkeypatch.setattr(
        "app.agent.repair_agent.build_reasoned_repair_plan",
        fake_plan,
    )

    class FakeReproduction:
        success = False
        combined_output = "different runtime output"

        def as_dict(self):
            return {
                "success": False,
                "combined_output": self.combined_output,
            }

    class FakeReproducer:
        def reproduce(self, **kwargs):
            return FakeReproduction()

    class FakePipelineResult:
        success = False
        stage = "test_completed"
        message = "test pipeline"

        def as_dict(self):
            return {
                "success": False,
                "stage": "test_completed",
                "message": "test pipeline",
            }

    class FakePipeline:
        def __init__(self):
            self.reproducer = FakeReproducer()

        def run(
            self,
            command,
            project_root,
            plan,
            approved,
        ):
            assert command
            assert project_root == str(project)
            assert plan
            assert approved is False

            return FakePipelineResult()

    agent = RepairAgent(
        pipeline=FakePipeline(),
    )

    result = agent.analyze_and_repair(
        command=command,
        project_root=str(project),
        error_text=supplied_error,
    )

    assert result.success is False
    assert result.stage == "test_completed"

    assert captured["diagnosis_error"] == supplied_error

    assert (
        captured["root_cause_error"]["error_type"]
        == "ModuleNotFoundError"
    )

    assert (
        captured["root_cause_error"]["message"]
        == "ModuleNotFoundError: No module named flask"
    )

    assert captured["plan_error"] == supplied_error

    assert result.repair_decisions

    decision = result.repair_decisions[0]

    assert decision["action"] == "verify_environment"
    assert decision["requires_approval"] is False


def test_repair_agent_returns_no_plan_when_planner_returns_empty(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "raise SystemExit(1)",
    ]

    monkeypatch.setattr(
        "app.agent.repair_agent.diagnose_error",
        lambda error: {
            "category": "unknown",
            "category_code": "unknown",
        },
    )

    monkeypatch.setattr(
        "app.agent.repair_agent.analyze_root_cause",
        lambda *args, **kwargs: {
            "category": "unknown",
            "reason": "Unknown failure.",
            "confidence": 0.1,
        },
    )

    monkeypatch.setattr(
        "app.agent.repair_agent.build_reasoned_repair_plan",
        lambda *args, **kwargs: [],
    )

    class FakeReproduction:
        success = False
        combined_output = "unknown failure"

        def as_dict(self):
            return {
                "success": False,
                "combined_output": self.combined_output,
            }

    class FakeReproducer:
        def reproduce(self, **kwargs):
            return FakeReproduction()

    class FakePipeline:
        def __init__(self):
            self.reproducer = FakeReproducer()

    result = RepairAgent(
        pipeline=FakePipeline(),
    ).analyze_and_repair(
        command=command,
        project_root=str(project),
    )

    assert result.success is False
    assert result.stage == "no_repair_plan"
    assert result.repair_plan == []
    assert result.repair_decisions == []
    assert result.pipeline is None


def test_repair_agent_passes_approval_to_pipeline(
    tmp_path,
    monkeypatch,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "raise SystemExit(1)",
    ]

    plan = [
        {
            "action": "verify_environment",
            "reason": "test",
        }
    ]

    monkeypatch.setattr(
        "app.agent.repair_agent.diagnose_error",
        lambda error: {
            "category": "test",
            "category_code": "test",
        },
    )

    monkeypatch.setattr(
        "app.agent.repair_agent.analyze_root_cause",
        lambda *args, **kwargs: {
            "reason": "Test failure.",
            "confidence": 0.5,
        },
    )

    monkeypatch.setattr(
        "app.agent.repair_agent.build_reasoned_repair_plan",
        lambda *args, **kwargs: plan,
    )

    class FakeReproduction:
        success = False
        combined_output = "test failure"

        def as_dict(self):
            return {
                "success": False,
                "combined_output": self.combined_output,
            }

    class FakeReproducer:
        def reproduce(self, **kwargs):
            return FakeReproduction()

    captured = {}

    class FakePipelineResult:
        success = True
        stage = "completed"
        message = "completed"

        def as_dict(self):
            return {
                "success": True,
                "stage": "completed",
                "message": "completed",
            }

    class FakePipeline:
        def __init__(self):
            self.reproducer = FakeReproducer()

        def run(self, **kwargs):
            captured.update(kwargs)
            return FakePipelineResult()

    result = RepairAgent(
        pipeline=FakePipeline(),
    ).analyze_and_repair(
        command=command,
        project_root=str(project),
        approved=True,
    )

    assert result.success is True
    assert result.stage == "completed"
    assert captured["approved"] is True
    assert captured["plan"] == plan


def test_repair_agent_builds_repair_decisions(
    tmp_path,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "import definitely_missing_package\n",
        encoding="utf-8",
    )

    agent = RepairAgent()

    result = agent.analyze_and_repair(
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

    assert result.repair_plan
    assert result.repair_decisions

    decision = result.repair_decisions[0]

    assert "action" in decision
    assert "reason" in decision
    assert "evidence" in decision
    assert "risk_level" in decision
    assert "requires_approval" in decision
    assert "verification_method" in decision


def test_repair_agent_decision_requires_approval_for_install(
    tmp_path,
    monkeypatch,
):
    app_file = tmp_path / "app.py"

    app_file.write_text(
        "import definitely_missing_package\n",
        encoding="utf-8",
    )

    pip_plan = [
        {
            "action": "pip_install",
            "package": "flask",
            "reason": "Install the missing Flask dependency.",
        }
    ]

    monkeypatch.setattr(
        "app.agent.repair_agent.build_reasoned_repair_plan",
        lambda *args, **kwargs: pip_plan,
    )

    agent = RepairAgent()

    result = agent.analyze_and_repair(
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

    assert result.repair_plan == pip_plan
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
    assert decision["verification_method"]
