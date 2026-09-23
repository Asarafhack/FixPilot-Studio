from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Sequence

from app.diagnostics.repair_pipeline import RepairPipeline
from app.agent.diagnostician import diagnose_error
from app.agent.error_fingerprint import fingerprint_error
from app.agent.root_cause import analyze_root_cause
from app.repair.planner import build_reasoned_repair_plan
from app.repair.decision import build_repair_decision


@dataclass
class RepairAgentResult:
    command: list[str]
    project_root: str

    reproduction: Optional[dict]
    diagnosis: Optional[dict]
    fingerprint: Optional[dict]
    root_cause: Optional[dict]
    repair_plan: Optional[list]
    repair_decisions: Optional[list]

    pipeline: Optional[dict]

    success: bool
    stage: str
    message: str

    def as_dict(self) -> dict:
        return asdict(self)


class RepairAgent:
    def __init__(
        self,
        pipeline: Optional[RepairPipeline] = None,
    ):
        self.pipeline = (
            pipeline
            or RepairPipeline()
        )

    def _build_repair_decisions(
        self,
        repair_plan: list,
        diagnosis: dict,
        fingerprint: dict,
        root_cause: dict,
    ) -> list[dict]:
        """
        Convert a technical repair plan into human-readable
        repair decisions.

        This method performs no system action.
        """

        decisions = []

        category = diagnosis.get(
            "category",
            "Unknown failure",
        )

        category_code = diagnosis.get(
            "category_code",
            "unknown",
        )

        language = fingerprint.get(
            "language",
            "unknown",
        )

        root_cause_reason = root_cause.get(
            "reason",
            "FixPilot identified a likely root cause.",
        )

        root_cause_confidence = root_cause.get(
            "confidence"
        )

        for action_item in repair_plan:
            if not isinstance(action_item, dict):
                continue

            action = action_item.get("action")

            if not action:
                continue

            target = (
                action_item.get("package")
                or action_item.get("dependency")
                or action_item.get("module")
                or action_item.get("port")
                or action_item.get("path")
            )

            requires_approval = action in {
                "pip_install",
                "npm_install",
                "declare_dependency",
            }

            if action == "pip_install":
                reason = (
                    "The Python dependency appears to be "
                    "missing from the active environment."
                )

                evidence = [
                    f"Failure category: {category}.",
                    f"Category code: {category_code}.",
                    f"Detected language: {language}.",
                    root_cause_reason,
                    "The proposed action installs the required "
                    "Python package.",
                ]

                verification = (
                    "Re-run the original command and verify "
                    "the Python import succeeds."
                )

                risk_level = "low"

            elif action == "npm_install":
                reason = (
                    "The Node.js dependency appears to be "
                    "missing from the project environment."
                )

                evidence = [
                    f"Failure category: {category}.",
                    f"Category code: {category_code}.",
                    f"Detected language: {language}.",
                    root_cause_reason,
                    "The proposed action installs the required "
                    "Node.js package.",
                ]

                verification = (
                    "Re-run the original command and verify "
                    "the Node.js module resolves."
                )

                risk_level = "low"

            elif action == "declare_dependency":
                reason = (
                    "The dependency is available in the "
                    "environment but is not declared by the "
                    "project."
                )

                evidence = [
                    f"Failure category: {category}.",
                    f"Category code: {category_code}.",
                    root_cause_reason,
                    "The proposed action records the dependency "
                    "in the project configuration.",
                ]

                verification = (
                    "Re-run the original command and verify "
                    "the project remains functional."
                )

                risk_level = "medium"

            elif action == "verify_import":
                reason = (
                    "Verify that the required Python module "
                    "can be imported successfully."
                )

                evidence = [
                    "This is a verification-only action.",
                    root_cause_reason,
                ]

                verification = (
                    "Import the target module using the active "
                    "Python interpreter."
                )

                risk_level = "low"

            elif action == "verify_environment":
                reason = (
                    "Verify that the required development "
                    "environment is available."
                )

                evidence = [
                    "This is a verification-only action.",
                    f"Detected language: {language}.",
                ]

                verification = (
                    "Inspect the active development environment."
                )

                risk_level = "low"

            elif action == "inspect_port":
                reason = (
                    "Inspect the requested port to determine "
                    "whether another process is using it."
                )

                evidence = [
                    f"Failure category: {category}.",
                    "This is an inspection-only action.",
                ]

                verification = (
                    "Inspect the port state and confirm whether "
                    "the conflict remains."
                )

                risk_level = "low"

            elif action == "inspect_path":
                reason = (
                    "Inspect the requested filesystem path "
                    "without modifying it."
                )

                evidence = [
                    "This is an inspection-only action.",
                ]

                verification = (
                    "Verify whether the expected path exists."
                )

                risk_level = "low"

            else:
                reason = (
                    "FixPilot identified a supported repair "
                    "action for the detected failure."
                )

                evidence = [
                    f"Failure category: {category}.",
                    f"Category code: {category_code}.",
                    root_cause_reason,
                ]

                verification = (
                    "Re-run the original command."
                )

                risk_level = "low"

            decisions.append(
                build_repair_decision(
                    action=action,
                    reason=reason,
                    evidence=evidence,
                    risk_level=risk_level,
                    requires_approval=requires_approval,
                    verification_method=verification,
                    target=(
                        str(target)
                        if target is not None
                        else None
                    ),
                    confidence=root_cause_confidence,
                )
            )

        return decisions

    def analyze_and_repair(
        self,
        command: Sequence[str],
        project_root: str,
        error_text: Optional[str] = None,
        approved: bool = False,
    ) -> RepairAgentResult:
        command = list(command)

        reproduction = self.pipeline.reproducer.reproduce(
            command=command,
            project_root=project_root,
        )

        reproduction_dict = reproduction.as_dict()

        if reproduction.success:
            return RepairAgentResult(
                command=command,
                project_root=project_root,
                reproduction=reproduction_dict,
                diagnosis=None,
                fingerprint=None,
                root_cause=None,
                repair_plan=[],
                repair_decisions=[],
                pipeline=None,
                success=True,
                stage="already_resolved",
                message=(
                    "The command already succeeds. "
                    "No repair is required."
                ),
            )

        diagnostic_text = (
            error_text
            or reproduction.combined_output
        )

        diagnosis = diagnose_error(
            diagnostic_text
        )

        fingerprint = fingerprint_error(
            diagnostic_text
        )

        if fingerprint is None:
            return RepairAgentResult(
                command=command,
                project_root=project_root,
                reproduction=reproduction_dict,
                diagnosis=diagnosis,
                fingerprint=None,
                root_cause=None,
                repair_plan=[],
                repair_decisions=[],
                pipeline=None,
                success=False,
                stage="fingerprint_failed",
                message=(
                    "FixPilot reproduced the failure "
                    "but could not create an error fingerprint."
                ),
            )

        root_cause = analyze_root_cause(
            fingerprint
        )

        repair_plan = build_reasoned_repair_plan(
            diagnostic_text,
            project_root=project_root,
        )

        if not repair_plan:
            return RepairAgentResult(
                command=command,
                project_root=project_root,
                reproduction=reproduction_dict,
                diagnosis=diagnosis,
                fingerprint=fingerprint,
                root_cause=root_cause,
                repair_plan=[],
                repair_decisions=[],
                pipeline=None,
                success=False,
                stage="no_repair_plan",
                message=(
                    "FixPilot reproduced the failure but "
                    "could not create a supported repair plan."
                ),
            )

        repair_decisions = self._build_repair_decisions(
            repair_plan=repair_plan,
            diagnosis=diagnosis,
            fingerprint=fingerprint,
            root_cause=root_cause,
        )

        pipeline_result = self.pipeline.run(
            command=command,
            project_root=project_root,
            plan=repair_plan,
            approved=approved,
        )

        pipeline_dict = pipeline_result.as_dict()

        return RepairAgentResult(
            command=command,
            project_root=project_root,
            reproduction=reproduction_dict,
            diagnosis=diagnosis,
            fingerprint=fingerprint,
            root_cause=root_cause,
            repair_plan=repair_plan,
            repair_decisions=repair_decisions,
            pipeline=pipeline_dict,
            success=pipeline_result.success,
            stage=pipeline_result.stage,
            message=pipeline_result.message,
        )


def analyze_and_repair(
    command: Sequence[str],
    project_root: str,
    error_text: Optional[str] = None,
    approved: bool = False,
) -> dict:
    agent = RepairAgent()

    return agent.analyze_and_repair(
        command=command,
        project_root=project_root,
        error_text=error_text,
        approved=approved,
    ).as_dict()