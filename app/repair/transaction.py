from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from app.diagnostics.original_command_verifier import (
    OriginalCommandVerifier,
)
from app.repair.project_snapshot import ProjectSnapshotter
from app.repair.service import repair_and_verify


@dataclass
class RepairTransactionResult:
    """
    Complete record of one repair transaction.

    Flow:

        Before Snapshot
              ↓
        Existing V1.3 Repair
              ↓
        After Snapshot
              ↓
        Exact Original Command Verification
              ↓
        Final Result
    """

    repair_result: dict
    before_snapshot: dict
    after_snapshot: Optional[dict]
    changed: bool
    original_command_verification: Optional[dict]
    completed: bool
    status: str
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return {
            "repair_result": self.repair_result,
            "before_snapshot": self.before_snapshot,
            "after_snapshot": self.after_snapshot,
            "changed": self.changed,
            "original_command_verification": (
                self.original_command_verification
            ),
            "completed": self.completed,
            "status": self.status,
            "error": self.error,
        }


class RepairTransaction:
    """
    Safely wraps the existing V1.3 repair service.

    Adds:

    - pre-repair snapshot
    - post-repair snapshot
    - exact original command verification
    - final transaction state

    This class does not execute arbitrary commands itself.
    """

    def __init__(
        self,
        snapshotter: Optional[ProjectSnapshotter] = None,
        command_verifier: Optional[OriginalCommandVerifier] = None,
    ):
        self.snapshotter = (
            snapshotter or ProjectSnapshotter()
        )

        self.command_verifier = (
            command_verifier
            or OriginalCommandVerifier()
        )

    def execute(
        self,
        plan: list[dict],
        project_root: str,
        original_command: Optional[list[str]] = None,
        approved: bool = False,
    ) -> RepairTransactionResult:

        # --------------------------------------------------
        # 1. PRE-REPAIR SNAPSHOT
        # --------------------------------------------------

        before_snapshot = self.snapshotter.create(
            project_root
        )

        # --------------------------------------------------
        # 2. EXISTING SAFE REPAIR SERVICE
        # --------------------------------------------------

        try:
            repair_result = repair_and_verify(
                plan,
                cwd=project_root,
                original_command=original_command,
                approved=approved,
            )

        except Exception as exc:
            return RepairTransactionResult(
                repair_result={
                    "success": False,
                    "stage": "exception",
                    "message": str(exc),
                },
                before_snapshot=before_snapshot.as_dict(),
                after_snapshot=None,
                changed=False,
                original_command_verification=None,
                completed=False,
                status="exception",
                error=str(exc),
            )

        # --------------------------------------------------
        # 3. REPAIR FAILED / APPROVAL REQUIRED
        # --------------------------------------------------

        if not repair_result.get("success", False):
            return RepairTransactionResult(
                repair_result=repair_result,
                before_snapshot=before_snapshot.as_dict(),
                after_snapshot=None,
                changed=False,
                original_command_verification=None,
                completed=False,
                status=repair_result.get(
                    "stage",
                    "repair_failed",
                ),
                error=repair_result.get("message"),
            )

        # --------------------------------------------------
        # 4. POST-REPAIR SNAPSHOT
        # --------------------------------------------------

        after_snapshot = self.snapshotter.create(
            project_root
        )

        changed = (
            before_snapshot.fingerprint
            != after_snapshot.fingerprint
        )

        # --------------------------------------------------
        # 5. EXACT ORIGINAL COMMAND VERIFICATION
        # --------------------------------------------------

        command_verification = None

        if original_command:
            try:
                command_result = (
                    self.command_verifier.verify(
                        command=original_command,
                        project_root=project_root,
                    )
                )

                command_verification = (
                    command_result.as_dict()
                )

            except Exception as exc:
                command_verification = {
                    "success": False,
                    "failure_resolved": False,
                    "error": str(exc),
                }

                return RepairTransactionResult(
                    repair_result=repair_result,
                    before_snapshot=before_snapshot.as_dict(),
                    after_snapshot=after_snapshot.as_dict(),
                    changed=changed,
                    original_command_verification=(
                        command_verification
                    ),
                    completed=False,
                    status="original_command_failed",
                    error=str(exc),
                )

            # The repair transaction is successful only when
            # the exact original command now succeeds.
            if not command_verification.get(
                "failure_resolved",
                False,
            ):
                return RepairTransactionResult(
                    repair_result=repair_result,
                    before_snapshot=before_snapshot.as_dict(),
                    after_snapshot=after_snapshot.as_dict(),
                    changed=changed,
                    original_command_verification=(
                        command_verification
                    ),
                    completed=False,
                    status="verification_failed",
                    error=(
                        "The repair completed, but the "
                        "original command still fails."
                    ),
                )

        # --------------------------------------------------
        # 6. FINAL SUCCESS
        # --------------------------------------------------

        return RepairTransactionResult(
            repair_result=repair_result,
            before_snapshot=before_snapshot.as_dict(),
            after_snapshot=after_snapshot.as_dict(),
            changed=changed,
            original_command_verification=(
                command_verification
            ),
            completed=True,
            status="completed",
        )


def execute_repair_transaction(
    plan: list[dict],
    project_root: str,
    original_command: Optional[list[str]] = None,
    approved: bool = False,
) -> dict[str, Any]:

    transaction = RepairTransaction()

    return transaction.execute(
        plan=plan,
        project_root=project_root,
        original_command=original_command,
        approved=approved,
    ).as_dict()