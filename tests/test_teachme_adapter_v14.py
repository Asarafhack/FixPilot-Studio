from app.teachme.adapter import TeachMeUIAdapter
from app.teachme.engine import TutorialEngine, build_generic_tutorial


def make_engine():
    return TutorialEngine(build_generic_tutorial())


def test_snapshot_before_session_start():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    snapshot = adapter.snapshot()

    assert snapshot["state"] == "idle"
    assert snapshot["step"] == 0
    assert snapshot["total_steps"] == 4
    assert snapshot["user_action_required"] is False
    assert snapshot["title"] == "Capture the error"


def test_snapshot_after_start():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    engine.start_session()

    snapshot = adapter.snapshot()

    assert snapshot["state"] == "observe"
    assert snapshot["title"] == "Capture the error"
    assert snapshot["instruction"] is not None


def test_snapshot_after_explain_requires_user_action():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    engine.start_session()
    engine.observe()
    engine.explain()

    snapshot = adapter.snapshot()

    assert snapshot["state"] == "wait_for_user"
    assert snapshot["user_action_required"] is True
    assert snapshot["title"] == "Capture the error"


def test_action_required_matches_session_state():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    assert adapter.action_required() is False

    engine.start_session()
    engine.observe()
    engine.explain()

    assert adapter.action_required() is True


def test_current_instruction():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    engine.start_session()

    assert (
        adapter.current_instruction()
        == "Copy the complete terminal error into FixPilot."
    )


def test_current_target_hint():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    engine.start_session()

    assert adapter.current_target_hint() == "Terminal"


def test_completed_session_snapshot():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    engine.start_session()

    for _ in range(4):
        engine.observe()
        engine.explain()
        engine.user_completed_step()
        engine.check_result(True)
        engine.continue_session()

    snapshot = adapter.snapshot()

    assert snapshot["state"] == "completed"
    assert snapshot["finished"] is True
    assert snapshot["user_action_required"] is False


def test_snapshot_contains_screen_information():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    snapshot = adapter.snapshot()

    assert snapshot["screen"] is not None
    assert snapshot["screen"]["width"] > 0
    assert snapshot["screen"]["height"] > 0
    assert isinstance(snapshot["screen"]["cursor_x"], int)
    assert isinstance(snapshot["screen"]["cursor_y"], int)


def test_cursor_position_returns_screen_coordinates():
    engine = make_engine()
    adapter = TeachMeUIAdapter(engine)

    position = adapter.cursor_position()

    assert position is not None
    assert isinstance(position["x"], int)
    assert isinstance(position["y"], int)


def test_adapter_can_use_custom_screen_observer():
    class FakeScreenObserver:
        def as_dict(self):
            return {
                "width": 1920,
                "height": 1080,
                "cursor_x": 321,
                "cursor_y": 654,
                "platform": "Windows",
            }

    engine = make_engine()
    adapter = TeachMeUIAdapter(
        engine,
        screen_observer=FakeScreenObserver(),
    )

    snapshot = adapter.snapshot()

    assert snapshot["screen"]["cursor_x"] == 321
    assert snapshot["screen"]["cursor_y"] == 654


def test_screen_failure_does_not_break_teachme():
    class BrokenScreenObserver:
        def as_dict(self):
            raise RuntimeError("screen unavailable")

    engine = make_engine()
    adapter = TeachMeUIAdapter(
        engine,
        screen_observer=BrokenScreenObserver(),
    )

    snapshot = adapter.snapshot()

    assert snapshot["screen"] is None
    assert snapshot["title"] == "Capture the error"