from dataclasses import dataclass, field
from typing import Callable, List, Optional

from app.teachme.session import TeachMeSession, TeachMeStep


@dataclass
class TutorialStep:
    title: str
    instruction: str
    why: str = ""
    target_hint: str = ""
    success_check: Optional[Callable[[], bool]] = None


@dataclass
class TutorialState:
    index: int = 0
    completed: List[str] = field(default_factory=list)


class TutorialEngine:
    """Human-in-the-loop tutorial engine.

    The engine never clicks, types, or launches applications. The user performs
    each action and explicitly advances the tutorial.

    The engine now exposes the V1.4 TeachMeSession state machine while
    preserving the original TutorialEngine API.
    """

    def __init__(self, steps=None):
        self.steps = steps or []
        self.state = TutorialState()
        self.session = TeachMeSession(self._build_session_steps())

    def _build_session_steps(self):
        return [
            TeachMeStep(
                title=step.title,
                explanation=step.why,
                instruction=step.instruction,
                expected_result=step.target_hint or None,
                metadata={
                    "target_hint": step.target_hint,
                    "has_success_check": step.success_check is not None,
                },
            )
            for step in self.steps
        ]

    @property
    def current(self):
        if 0 <= self.state.index < len(self.steps):
            return self.steps[self.state.index]
        return None

    @property
    def progress(self):
        if not self.steps:
            return 1.0
        return self.state.index / len(self.steps)

    def start_session(self):
        """Start the V1.4 Teach Me state machine."""
        return self.session.start()

    def observe(self):
        """Observe the current tutorial step."""
        return self.session.observe()

    def explain(self):
        """Present the current instruction to the user."""
        return self.session.explain()

    def user_completed_step(self):
        """Record that the user says the step has been completed."""
        return self.session.user_completed_step()

    def check_result(self, success=None):
        """Check the current step result.

        If a legacy success_check callback exists and no explicit result is
        supplied, the callback is used.
        """
        if success is None:
            step = self.current

            if not step or not step.success_check:
                success = True
            else:
                try:
                    success = bool(step.success_check())
                except Exception:
                    success = False

        return self.session.check_result(bool(success))

    def continue_session(self):
        """Move the Teach Me session to the next step."""
        result = self.session.continue_session()

        if result["success"]:
            self._sync_legacy_state()

        return result

    def next(self):
        """Preserve the original TutorialEngine next() API."""
        step = self.current

        if step:
            self.state.completed.append(step.title)
            self.state.index += 1

        return self.current

    def back(self):
        """Preserve the original TutorialEngine back() API."""
        if self.state.index > 0:
            self.state.index -= 1

            if self.state.completed:
                self.state.completed.pop()

        self._sync_session_index()

        return self.current

    def reset(self):
        """Reset both legacy tutorial state and V1.4 session state."""
        self.state = TutorialState()
        self.session.reset()

    def is_finished(self):
        return self.current is None

    def check_current(self):
        """Preserve the original success-check API."""
        step = self.current

        if not step or not step.success_check:
            return None

        try:
            return bool(step.success_check())
        except Exception:
            return False

    def retry(self):
        """Retry the current Teach Me step after a failed verification."""
        return self.session.retry()

    def _sync_legacy_state(self):
        """Synchronize the legacy index with the V1.4 session."""
        self.state.index = self.session.current_index

        completed_titles = [
            step.title
            for step in self.steps[:self.state.index]
        ]

        self.state.completed = completed_titles

    def _sync_session_index(self):
        """Synchronize the V1.4 session index with legacy navigation."""
        self.session.current_index = self.state.index


def build_python_dependency_tutorial(package):
    return [
        TutorialStep(
            "Open the project terminal",
            "Open the integrated terminal in VS Code.",
            "FixPilot needs the same project environment that produced the error.",
            "VS Code → Terminal → New Terminal"
        ),
        TutorialStep(
            "Check the Python interpreter",
            "Look at the terminal prompt and confirm the intended virtual environment is active.",
            "Installing into the wrong Python environment can leave the original error unchanged.",
            "VS Code Python interpreter / terminal prompt"
        ),
        TutorialStep(
            "Inspect the dependency declaration",
            f"Open requirements.txt or pyproject.toml and check whether '{package}' is already declared.",
            "The project manifest is the source of truth before adding a new dependency.",
            "Project Explorer → requirements.txt / pyproject.toml"
        ),
        TutorialStep(
            "Install the approved dependency",
            f"Run the approved package installation in the project terminal for '{package}'.",
            "You perform the command yourself; FixPilot does not type or execute it in Teach Me mode.",
            "Integrated terminal"
        ),
        TutorialStep(
            "Re-run the application",
            "Run the same command that originally failed.",
            "A repair is useful only if the original failure is resolved.",
            "Integrated terminal / Run and Debug"
        ),
        TutorialStep(
            "Confirm the result",
            "Confirm that the original error is gone. If it remains, return to FixPilot for another diagnosis.",
            "Verification closes the repair loop.",
            "Terminal output"
        ),
    ]


def build_generic_tutorial():
    return [
        TutorialStep(
            "Capture the error",
            "Copy the complete terminal error into FixPilot.",
            "The full error gives the diagnosis engine more context.",
            "Terminal"
        ),
        TutorialStep(
            "Inspect the suggested cause",
            "Read the diagnosis and project evidence before changing anything.",
            "Understanding the cause helps avoid unnecessary changes.",
            "FixPilot Analysis"
        ),
        TutorialStep(
            "Perform the approved action",
            "Follow the displayed repair instruction yourself.",
            "Teach Me mode keeps the human in control of every computer action.",
            "Terminal / Settings / Editor"
        ),
        TutorialStep(
            "Verify",
            "Re-run the failing workflow and confirm the result.",
            "Verification distinguishes a real fix from a change that only looks successful.",
            "Terminal / application"
        ),
    ]