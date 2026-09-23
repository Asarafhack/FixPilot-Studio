from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Optional


@dataclass
class RepairDecision:
    """
    Human-readable explanation of why FixPilot proposes
    a particular repair.

    This object does not execute anything.
    It only describes the proposed decision.
    """

    action: str
    reason: str
    evidence: list[str]
    risk_level: str
    requires_approval: bool
    verification_method: str
    target: Optional[str] = None
    confidence: Optional[float] = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_repair_decision(
    action: str,
    reason: str,
    evidence: list[str],
    risk_level: str = "low",
    requires_approval: bool = True,
    verification_method: str = "Re-run the original command.",
    target: Optional[str] = None,
    confidence: Optional[float] = None,
) -> dict[str, Any]:
    """
    Build a structured repair decision.

    This function intentionally performs no system action.
    """

    if not isinstance(action, str) or not action.strip():
        raise ValueError("action must be a non-empty string.")

    if not isinstance(reason, str) or not reason.strip():
        raise ValueError("reason must be a non-empty string.")

    if not isinstance(evidence, list):
        raise ValueError("evidence must be a list.")

    if any(
        not isinstance(item, str) or not item.strip()
        for item in evidence
    ):
        raise ValueError(
            "Every evidence item must be a non-empty string."
        )

    allowed_risk_levels = {
        "low",
        "medium",
        "high",
    }

    risk_level = risk_level.lower().strip()

    if risk_level not in allowed_risk_levels:
        raise ValueError(
            "risk_level must be low, medium, or high."
        )

    if confidence is not None:
        if not isinstance(confidence, (int, float)):
            raise ValueError(
                "confidence must be numeric."
            )

        if not 0.0 <= float(confidence) <= 1.0:
            raise ValueError(
                "confidence must be between 0.0 and 1.0."
            )

    return RepairDecision(
        action=action.strip(),
        reason=reason.strip(),
        evidence=evidence,
        risk_level=risk_level,
        requires_approval=bool(requires_approval),
        verification_method=verification_method.strip(),
        target=(
            target.strip()
            if isinstance(target, str)
            else target
        ),
        confidence=(
            float(confidence)
            if confidence is not None
            else None
        ),
    ).as_dict()