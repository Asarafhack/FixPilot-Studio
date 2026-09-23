from __future__ import annotations

from typing import Any

from app.teachme.engine import TutorialEngine
from app.teachme.screen import ScreenObserver


class TeachMeUIAdapter:
    """Convert Teach Me engine and screen state into UI-safe data.

    This adapter only reads state. It never moves the pointer, clicks,
    types, launches applications, or executes commands.
    """

    def __init__(
        self,
        engine: TutorialEngine,
        screen_observer: ScreenObserver | None = None,
    ):
        self.engine = engine
        self.screen_observer = screen_observer or ScreenObserver()

    def snapshot(self) -> dict[str, Any]:
        session = self.engine.session
        step = self.engine.current

        result: dict[str, Any] = {
            "state": session.state.value,
            "step": session.current_index,
            "total_steps": len(self.engine.steps),
            "progress": self.engine.progress,
            "completed": session.completed,
            "finished": self.engine.is_finished(),
            "user_action_required": False,
            "title": None,
            "instruction": None,
            "why": None,
            "target_hint": None,
            "expected_result": None,
            "screen": None,
        }

        if step is not None:
            result.update(
                {
                    "title": step.title,
                    "instruction": step.instruction,
                    "why": step.why,
                    "target_hint": step.target_hint,
                    "expected_result": step.target_hint or None,
                    "user_action_required": (
                        session.state.value == "wait_for_user"
                    ),
                }
            )

        result["screen"] = self._screen_snapshot()

        return result

    def _screen_snapshot(self) -> dict[str, Any] | None:
        try:
            return self.screen_observer.as_dict()
        except (RuntimeError, OSError):
            return None

    def action_required(self) -> bool:
        return self.engine.session.state.value == "wait_for_user"

    def current_instruction(self) -> str | None:
        step = self.engine.current

        if step is None:
            return None

        return step.instruction

    def current_target_hint(self) -> str | None:
        step = self.engine.current

        if step is None:
            return None

        return step.target_hint

    def cursor_position(self) -> dict[str, int] | None:
        screen = self._screen_snapshot()

        if screen is None:
            return None

        return {
            "x": screen["cursor_x"],
            "y": screen["cursor_y"],
        }