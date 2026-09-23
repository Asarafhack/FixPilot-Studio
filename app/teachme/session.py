from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TeachMeState(str, Enum):
    IDLE = "idle"
    OBSERVE = "observe"
    EXPLAIN = "explain"
    WAIT_FOR_USER = "wait_for_user"
    CHECK_RESULT = "check_result"
    NEXT_STEP = "next_step"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TeachMeStep:
    title: str
    explanation: str
    instruction: str
    expected_result: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class TeachMeSession:
    """
    Controls a safe, user-driven Teach Me workflow.

    The AI may describe and validate steps, but the session does not
    automatically perform arbitrary computer actions.
    """

    def __init__(self, steps: list[TeachMeStep] | None = None):
        self.steps = steps or []
        self.current_index = 0
        self.state = TeachMeState.IDLE
        self.history: list[dict[str, Any]] = []

    @property
    def current_step(self) -> TeachMeStep | None:
        if 0 <= self.current_index < len(self.steps):
            return self.steps[self.current_index]

        return None

    @property
    def completed(self) -> bool:
        return self.state == TeachMeState.COMPLETED

    def start(self) -> dict[str, Any]:
        if not self.steps:
            self.state = TeachMeState.COMPLETED
            return self._result("No Teach Me steps are required.")

        self.current_index = 0
        self.state = TeachMeState.OBSERVE

        return self._result("Teach Me session started.")

    def observe(self) -> dict[str, Any]:
        if self.state not in {
            TeachMeState.OBSERVE,
            TeachMeState.NEXT_STEP,
        }:
            return self._invalid_transition()

        if self.current_step is None:
            self.state = TeachMeState.COMPLETED
            return self._result("Teach Me session completed.")

        self.state = TeachMeState.EXPLAIN

        return self._result(
            "Current step observed.",
            step=self.current_step,
        )

    def explain(self) -> dict[str, Any]:
        if self.state != TeachMeState.EXPLAIN:
            return self._invalid_transition()

        if self.current_step is None:
            self.state = TeachMeState.COMPLETED
            return self._result("Teach Me session completed.")

        self.state = TeachMeState.WAIT_FOR_USER

        return self._result(
            "Instruction presented to the user.",
            step=self.current_step,
        )

    def user_completed_step(self) -> dict[str, Any]:
        if self.state != TeachMeState.WAIT_FOR_USER:
            return self._invalid_transition()

        self.state = TeachMeState.CHECK_RESULT

        return self._result(
            "Waiting for result verification."
        )

    def check_result(self, success: bool) -> dict[str, Any]:
        if self.state != TeachMeState.CHECK_RESULT:
            return self._invalid_transition()

        if not success:
            self.state = TeachMeState.FAILED

            return self._result(
                "The expected result was not detected."
            )

        self.state = TeachMeState.NEXT_STEP

        return self._result(
            "Step completed successfully."
        )

    def continue_session(self) -> dict[str, Any]:
        if self.state != TeachMeState.NEXT_STEP:
            return self._invalid_transition()

        self.current_index += 1

        if self.current_index >= len(self.steps):
            self.state = TeachMeState.COMPLETED

            return self._result(
                "All Teach Me steps completed."
            )

        self.state = TeachMeState.OBSERVE

        return self._result(
            "Moving to the next step.",
            step=self.current_step,
        )

    def retry(self) -> dict[str, Any]:
        if self.state != TeachMeState.FAILED:
            return self._invalid_transition()

        self.state = TeachMeState.WAIT_FOR_USER

        return self._result(
            "Retrying the current step.",
            step=self.current_step,
        )

    def reset(self) -> dict[str, Any]:
        self.current_index = 0
        self.state = TeachMeState.IDLE
        self.history.clear()

        return self._result("Teach Me session reset.")

    def _invalid_transition(self) -> dict[str, Any]:
        return self._result(
            f"Invalid state transition from '{self.state.value}'.",
            success=False,
        )

    def _result(
        self,
        message: str,
        success: bool = True,
        step: TeachMeStep | None = None,
    ) -> dict[str, Any]:
        result = {
            "success": success,
            "state": self.state.value,
            "message": message,
            "step_index": self.current_index,
            "total_steps": len(self.steps),
        }

        if step is not None:
            result["step"] = {
                "title": step.title,
                "explanation": step.explanation,
                "instruction": step.instruction,
                "expected_result": step.expected_result,
                "metadata": step.metadata,
            }

        self.history.append(result.copy())

        return result