from app.repair.transaction import RepairTransaction


class FakeSnapshot:
    def __init__(self, fingerprint):
        self.fingerprint = fingerprint

    def as_dict(self):
        return {
            "fingerprint": self.fingerprint,
        }


class FakeSnapshotter:
    def __init__(self):
        self.calls = 0

    def create(self, project_root):
        self.calls += 1

        if self.calls == 1:
            return FakeSnapshot("before")

        return FakeSnapshot("after")


class FakeCommandResult:
    def __init__(
        self,
        success,
        failure_resolved,
    ):
        self.success = success
        self.failure_resolved = failure_resolved

    def as_dict(self):
        return {
            "success": self.success,
            "failure_resolved": self.failure_resolved,
        }


class FakeCommandVerifier:
    def __init__(
        self,
        success=True,
        failure_resolved=True,
    ):
        self.success = success
        self.failure_resolved = failure_resolved
        self.command = None
        self.project_root = None

    def verify(
        self,
        command,
        project_root,
    ):
        self.command = command
        self.project_root = project_root

        return FakeCommandResult(
            success=self.success,
            failure_resolved=self.failure_resolved,
        )


def test_transaction_completes_when_original_command_is_fixed(
    tmp_path,
    monkeypatch,
):
    snapshotter = FakeSnapshotter()

    verifier = FakeCommandVerifier(
        success=True,
        failure_resolved=True,
    )

    def fake_repair_and_verify(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        assert approved is True

        return {
            "success": True,
            "stage": "completed",
            "message": "Repair completed.",
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair_and_verify,
    )

    transaction = RepairTransaction(
        snapshotter=snapshotter,
        command_verifier=verifier,
    )

    original_command = [
        "py",
        "app.py",
        "--mode",
        "production",
    ]

    result = transaction.execute(
        plan=[
            {
                "action": "pip_install",
                "package": "example-package",
            }
        ],
        project_root=str(tmp_path),
        original_command=original_command,
        approved=True,
    )

    assert result.completed is True
    assert result.status == "completed"
    assert result.error is None

    assert result.changed is True

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

    assert verifier.command == original_command
    assert (
        verifier.project_root
        == str(tmp_path)
    )

    assert snapshotter.calls == 2


def test_transaction_fails_when_original_command_still_fails(
    tmp_path,
    monkeypatch,
):
    snapshotter = FakeSnapshotter()

    verifier = FakeCommandVerifier(
        success=False,
        failure_resolved=False,
    )

    def fake_repair_and_verify(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        return {
            "success": True,
            "stage": "completed",
            "message": "Repair execution completed.",
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair_and_verify,
    )

    transaction = RepairTransaction(
        snapshotter=snapshotter,
        command_verifier=verifier,
    )

    result = transaction.execute(
        plan=[
            {
                "action": "pip_install",
                "package": "example-package",
            }
        ],
        project_root=str(tmp_path),
        original_command=[
            "py",
            "app.py",
        ],
        approved=True,
    )

    assert result.completed is False
    assert result.status == "verification_failed"

    assert (
        result.error
        == (
            "The repair completed, but the "
            "original command still fails."
        )
    )

    assert (
        result.original_command_verification[
            "failure_resolved"
        ]
        is False
    )


def test_transaction_stops_when_approval_is_not_granted(
    tmp_path,
    monkeypatch,
):
    snapshotter = FakeSnapshotter()

    verifier = FakeCommandVerifier()

    def fake_repair_and_verify(
        plan,
        cwd=None,
        original_command=None,
        approved=False,
    ):
        assert approved is False

        return {
            "success": False,
            "stage": "approval_required",
            "message": "User approval is required.",
        }

    monkeypatch.setattr(
        "app.repair.transaction.repair_and_verify",
        fake_repair_and_verify,
    )

    transaction = RepairTransaction(
        snapshotter=snapshotter,
        command_verifier=verifier,
    )

    result = transaction.execute(
        plan=[
            {
                "action": "pip_install",
                "package": "example-package",
            }
        ],
        project_root=str(tmp_path),
        original_command=[
            "py",
            "app.py",
        ],
        approved=False,
    )

    assert result.completed is False
    assert result.status == "approval_required"

    assert result.original_command_verification is None

    assert verifier.command is None
    assert snapshotter.calls == 1
