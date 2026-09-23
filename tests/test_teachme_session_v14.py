from app.teachme.session import (
    TeachMeSession,
    TeachMeState,
    TeachMeStep,
)


def make_steps():
    return [
        TeachMeStep(
            title="Open terminal",
            explanation="The terminal is where the repair command will be executed.",
            instruction="Open the integrated VS Code terminal.",
            expected_result="Terminal is visible.",
        ),
        TeachMeStep(
            title="Install dependency",
            explanation="The project requires Flask but it is not installed.",
            instruction="Run: pip install flask",
            expected_result="Flask installation completes successfully.",
        ),
    ]


def test_session_starts_in_idle():
    session = TeachMeSession(make_steps())

    assert session.state == TeachMeState.IDLE
    assert session.current_index == 0


def test_session_start_moves_to_observe():
    session = TeachMeSession(make_steps())

    result = session.start()

    assert result["success"] is True
    assert session.state == TeachMeState.OBSERVE
    assert session.current_index == 0


def test_observe_moves_to_explain():
    session = TeachMeSession(make_steps())
    session.start()

    result = session.observe()

    assert result["success"] is True
    assert session.state == TeachMeState.EXPLAIN
    assert result["step"]["title"] == "Open terminal"


def test_explain_waits_for_user():
    session = TeachMeSession(make_steps())
    session.start()
    session.observe()

    result = session.explain()

    assert result["success"] is True
    assert session.state == TeachMeState.WAIT_FOR_USER


def test_user_completion_moves_to_result_check():
    session = TeachMeSession(make_steps())
    session.start()
    session.observe()
    session.explain()

    result = session.user_completed_step()

    assert result["success"] is True
    assert session.state == TeachMeState.CHECK_RESULT


def test_successful_result_moves_to_next_step():
    session = TeachMeSession(make_steps())
    session.start()
    session.observe()
    session.explain()
    session.user_completed_step()

    result = session.check_result(True)

    assert result["success"] is True
    assert session.state == TeachMeState.NEXT_STEP


def test_continue_moves_to_next_step():
    session = TeachMeSession(make_steps())
    session.start()
    session.observe()
    session.explain()
    session.user_completed_step()
    session.check_result(True)

    result = session.continue_session()

    assert result["success"] is True
    assert session.current_index == 1
    assert session.state == TeachMeState.OBSERVE


def test_complete_entire_session():
    session = TeachMeSession(make_steps())
    session.start()

    for _ in range(2):
        session.observe()
        session.explain()
        session.user_completed_step()
        session.check_result(True)
        session.continue_session()

    assert session.completed is True
    assert session.state == TeachMeState.COMPLETED


def test_failed_result_can_be_retried():
    session = TeachMeSession(make_steps())
    session.start()
    session.observe()
    session.explain()
    session.user_completed_step()

    result = session.check_result(False)

    assert result["success"] is True
    assert session.state == TeachMeState.FAILED

    retry_result = session.retry()

    assert retry_result["success"] is True
    assert session.state == TeachMeState.WAIT_FOR_USER


def test_invalid_transition_is_rejected():
    session = TeachMeSession(make_steps())

    result = session.explain()

    assert result["success"] is False
    assert session.state == TeachMeState.IDLE


def test_empty_session_completes():
    session = TeachMeSession([])

    result = session.start()

    assert result["success"] is True
    assert session.state == TeachMeState.COMPLETED
    assert session.completed is True


def test_reset_returns_to_idle():
    session = TeachMeSession(make_steps())
    session.start()
    session.observe()

    result = session.reset()

    assert result["success"] is True
    assert session.state == TeachMeState.IDLE
    assert session.current_index == 0
    assert len(session.history) == 1
    assert session.history[0]["message"] == "Teach Me session reset."