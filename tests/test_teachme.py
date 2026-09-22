from app.teachme import TutorialEngine, TutorialStep
from app.teachme.engine import build_generic_tutorial, build_python_dependency_tutorial

def test_tutorial_progression():
    engine = TutorialEngine([TutorialStep("One", "Do one"), TutorialStep("Two", "Do two")])
    assert engine.current.title == "One"
    engine.next()
    assert engine.current.title == "Two"
    engine.next()
    assert engine.is_finished()

def test_python_tutorial_has_human_install_step():
    steps = build_python_dependency_tutorial("flask")
    assert any("Install the approved dependency" in step.title for step in steps)
    assert all(step.success_check is None for step in steps)

def test_generic_tutorial_exists():
    assert len(build_generic_tutorial()) >= 3
