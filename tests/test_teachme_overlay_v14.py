
import tkinter as tk

import pytest

from app.teachme.overlay import CursorGuideOverlay
from app.teachme.engine import TutorialEngine, build_generic_tutorial
from app.teachme.adapter import TeachMeUIAdapter


@pytest.fixture
def overlay():
    root = tk.Tk()
    root.withdraw()

    guide = CursorGuideOverlay(root)

    yield root, guide

    try:
        guide.close()
    except tk.TclError:
        pass

    try:
        root.update_idletasks()
    except tk.TclError:
        pass

    try:
        root.destroy()
    except tk.TclError:
        pass

    try:
        root.quit()
    except tk.TclError:
        pass


def test_overlay_can_be_created(overlay):
    root, guide = overlay

    assert guide.window.winfo_exists()


def test_overlay_updates_from_tutorial_step(overlay):
    root, guide = overlay

    engine = TutorialEngine(build_generic_tutorial())
    step = engine.current

    guide.update(step)

    assert guide.title.cget("text") == "Capture the error"
    assert "Copy the complete terminal error" in (
        guide.instruction.cget("text")
    )


def test_overlay_updates_from_snapshot(overlay):
    root, guide = overlay

    engine = TutorialEngine(build_generic_tutorial())
    adapter = TeachMeUIAdapter(engine)

    engine.start_session()
    engine.observe()
    engine.explain()

    snapshot = adapter.snapshot()

    guide.update(snapshot=snapshot)

    assert guide.title.cget("text") == "Capture the error"
    assert guide.status.cget("text") == "Your action is required."


def test_overlay_displays_target_and_reason(overlay):
    root, guide = overlay

    engine = TutorialEngine(build_generic_tutorial())
    adapter = TeachMeUIAdapter(engine)

    engine.start_session()
    engine.observe()
    engine.explain()

    guide.update(snapshot=adapter.snapshot())

    assert "Why:" in guide.why.cget("text")
    assert "Target:" in guide.target.cget("text")


def test_overlay_displays_cursor_position(overlay):
    root, guide = overlay

    engine = TutorialEngine(build_generic_tutorial())

    guide.update(
        engine.current,
        cursor_position={"x": 500, "y": 300},
    )

    assert guide.cursor.cget("text") == "Pointer: X=500 Y=300"


def test_overlay_displays_completed_state(overlay):
    root, guide = overlay

    guide.update(
        snapshot={
            "state": "completed",
            "step": 4,
            "total_steps": 4,
            "progress": 1.0,
            "finished": True,
            "user_action_required": False,
            "title": None,
            "instruction": None,
            "why": None,
            "target_hint": None,
            "expected_result": None,
        }
    )

    assert guide.title.cget("text") == "Teach Me Complete"
    assert guide.status.cget("text") == "Completed"


def test_overlay_does_not_require_cursor_control(overlay):
    root, guide = overlay

    assert not hasattr(guide, "move_cursor")
    assert not hasattr(guide, "click")
    assert not hasattr(guide, "type_text")


def test_overlay_can_use_adapter_for_snapshot(overlay):
    root, guide = overlay

    engine = TutorialEngine(build_generic_tutorial())
    adapter = TeachMeUIAdapter(engine)

    guide.adapter = adapter

    engine.start_session()
    engine.observe()
    engine.explain()

    snapshot = guide.refresh_from_adapter()

    assert snapshot["state"] == "wait_for_user"
    assert guide.title.cget("text") == "Capture the error"
    assert guide.status.cget("text") == "Your action is required."


def test_overlay_reads_cursor_from_adapter(overlay):
    root, guide = overlay

    class FakeAdapter:
        def snapshot(self):
            return {
                "state": "wait_for_user",
                "step": 0,
                "total_steps": 1,
                "progress": 0.0,
                "finished": False,
                "title": "Test step",
                "instruction": "Perform the test action.",
                "why": "Testing cursor integration.",
                "target_hint": "Terminal",
                "expected_result": "Done",
            }

        def cursor_position(self):
            return {"x": 742, "y": 418}

    guide.adapter = FakeAdapter()

    snapshot = guide.refresh_from_adapter()

    assert snapshot["title"] == "Test step"
    assert guide.cursor.cget("text") == "Pointer: X=742 Y=418"


def test_overlay_handles_adapter_cursor_failure(overlay):
    root, guide = overlay

    class BrokenAdapter:
        def snapshot(self):
            return {
                "state": "wait_for_user",
                "step": 0,
                "total_steps": 1,
                "progress": 0.0,
                "finished": False,
                "title": "Test step",
                "instruction": "Perform the test action.",
                "why": "",
                "target_hint": "",
                "expected_result": None,
            }

        def cursor_position(self):
            raise RuntimeError("cursor unavailable")

    guide.adapter = BrokenAdapter()

    guide.refresh_from_adapter()

    assert guide.cursor.cget("text") == "Pointer: unavailable"

