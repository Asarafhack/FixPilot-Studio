from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Sequence

from app.diagnostics.reproducer import FailureReproducer
from app.repair.transaction import RepairTransaction


@dataclass
class RepairPipelineResult:
    """
    Complete result of:

        Reproduce → Repair → Verify
    """

    reproduced: bool
    reproduction: Optional[dict]

    repair_attempted: bool
    transaction: Optional[dict]

    success: bool
    stage: str
    message: str

    def as_dict(self) -> dict:
        return asdict(self)


class RepairPipeline:
    """
    Production orchestration layer for the V1.5 repair flow.

    Responsibilities:

    1. Reproduce the original failure.
    2. Refuse repair when the failure cannot be reproduced.
    3. Execute the existing safe repair transaction.
    4. Re-run the exact original command.
    5. Return one structured result.

    This class does not provide arbitrary shell execution.
    """

    def __init__(
        self,
        reproducer: Optional[FailureReproducer] = None,
        transaction: Optional[RepairTransaction] = None,
        timeout: int = 30,
    ):
        self.reproducer = (
            reproducer
            or FailureReproducer(timeout=timeout)
        )

        self.transaction = (
            transaction
            or RepairTransaction()
        )

    def run(
        self,
        command: Sequence[str],
        project_root: str,
        plan: list[dict],
        approved: bool = False,
    ) -> RepairPipelineResult:

        # --------------------------------------------------
        # 1. REPRODUCE ORIGINAL FAILURE
        # --------------------------------------------------

        reproduction = self.reproducer.reproduce(
            command=command,
            project_root=project_root,
        )

        reproduction_dict = reproduction.as_dict()

        # --------------------------------------------------
        # 2. ORIGINAL COMMAND ALREADY WORKS
        # --------------------------------------------------

        if reproduction.success:
            return RepairPipelineResult(
                reproduced=False,
                reproduction=reproduction_dict,
                repair_attempted=False,
                transaction=None,
                success=True,
                stage="already_resolved",
                message=(
                    "The original command already succeeds. "
                    "No repair was required."
                ),
            )

        # --------------------------------------------------
        # 3. FAILURE CONFIRMED
        # --------------------------------------------------

        transaction_result = self.transaction.execute(
            plan=plan,
            project_root=project_root,
            original_command=list(command),
            approved=approved,
        )

        transaction_dict = transaction_result.as_dict()

        # --------------------------------------------------
        # 4. REPAIR COMPLETED + VERIFIED
        # --------------------------------------------------

        if transaction_result.completed:
            return RepairPipelineResult(
                reproduced=True,
                reproduction=reproduction_dict,
                repair_attempted=True,
                transaction=transaction_dict,
                success=True,
                stage="completed",
                message=(
                    "Failure reproduced, repair executed, "
                    "and the original command was verified "
                    "successfully."
                ),
            )

        # --------------------------------------------------
        # 5. REPAIR DID NOT COMPLETE
        # --------------------------------------------------

        return RepairPipelineResult(
            reproduced=True,
            reproduction=reproduction_dict,
            repair_attempted=True,
            transaction=transaction_dict,
            success=False,
            stage=transaction_result.status,
            message=(
                transaction_result.error
                or "Repair transaction did not complete."
            ),
        )


def run_repair_pipeline(
    command: Sequence[str],
    project_root: str,
    plan: list[dict],
    approved: bool = False,
    timeout: int = 30,
) -> dict:
    """
    Convenience wrapper for the production pipeline.
    """

    pipeline = RepairPipeline(
        timeout=timeout,
    )

    return pipeline.run(
        command=command,
        project_root=project_root,
        plan=plan,
        approved=approved,
    ).as_dict()