from app.diagnostics.repair_pipeline import RepairPipeline


def test_pipeline_detects_existing_success(tmp_path):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "print('already works')",
    ]

    plan = []

    result = RepairPipeline().run(
        command=command,
        project_root=str(project),
        plan=plan,
    )

    assert result.success is True
    assert result.stage == "already_resolved"
    assert result.repair_attempted is False
    assert result.reproduced is False


def test_pipeline_reproduces_failure_and_repairs(
    tmp_path,
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
            "reason": "test repair",
        }
    ]

    class FakeTransactionResult:
        completed = True
        status = "completed"
        error = None

        def as_dict(self):
            return {
                "completed": True,
                "status": "completed",
            }

    class FakeTransaction:
        def execute(self, **kwargs):
            return FakeTransactionResult()

    pipeline = RepairPipeline(
        transaction=FakeTransaction()
    )

    result = pipeline.run(
        command=command,
        project_root=str(project),
        plan=plan,
        approved=True,
    )

    assert result.success is True
    assert result.stage == "completed"
    assert result.reproduced is True
    assert result.repair_attempted is True
    assert result.transaction is not None


def test_pipeline_returns_failed_transaction(
    tmp_path,
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
            "reason": "test repair",
        }
    ]

    class FakeTransactionResult:
        completed = False
        status = "verification_failed"
        error = "Original command still fails."

        def as_dict(self):
            return {
                "completed": False,
                "status": "verification_failed",
                "error": self.error,
            }

    class FakeTransaction:
        def execute(self, **kwargs):
            return FakeTransactionResult()

    pipeline = RepairPipeline(
        transaction=FakeTransaction()
    )

    result = pipeline.run(
        command=command,
        project_root=str(project),
        plan=plan,
        approved=True,
    )

    assert result.success is False
    assert result.stage == "verification_failed"
    assert result.reproduced is True
    assert result.repair_attempted is True


def test_pipeline_passes_original_command_to_transaction(
    tmp_path,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "raise SystemExit(1)",
    ]

    captured = {}

    class FakeTransactionResult:
        completed = True
        status = "completed"
        error = None

        def as_dict(self):
            return {
                "completed": True,
                "status": "completed",
            }

    class FakeTransaction:
        def execute(self, **kwargs):
            captured.update(kwargs)
            return FakeTransactionResult()

    pipeline = RepairPipeline(
        transaction=FakeTransaction()
    )

    pipeline.run(
        command=command,
        project_root=str(project),
        plan=[],
        approved=True,
    )

    assert captured["original_command"] == command
    assert captured["project_root"] == str(project)
    assert captured["approved"] is True


def test_pipeline_preserves_reproduction_details(
    tmp_path,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "import sys; print('failure'); sys.exit(7)",
    ]

    class FakeTransactionResult:
        completed = False
        status = "repair_failed"
        error = "test failure"

        def as_dict(self):
            return {
                "completed": False,
                "status": "repair_failed",
            }

    class FakeTransaction:
        def execute(self, **kwargs):
            return FakeTransactionResult()

    pipeline = RepairPipeline(
        transaction=FakeTransaction()
    )

    result = pipeline.run(
        command=command,
        project_root=str(project),
        plan=[],
    )

    assert result.reproduction is not None
    assert result.reproduction["exit_code"] == 7
    assert (
        "failure"
        in result.reproduction["combined_output"]
    )


def test_pipeline_convenience_wrapper(
    tmp_path,
):
    project = tmp_path / "project"
    project.mkdir()

    command = [
        "py",
        "-c",
        "print('wrapper works')",
    ]

    from app.diagnostics.repair_pipeline import (
        run_repair_pipeline,
    )

    result = run_repair_pipeline(
        command=command,
        project_root=str(project),
        plan=[],
    )

    assert isinstance(result, dict)
    assert result["success"] is True
    assert result["stage"] == "already_resolved"