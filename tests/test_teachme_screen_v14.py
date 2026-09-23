import platform

import pytest

from app.teachme.screen import ScreenObserver, ScreenSnapshot


def test_screen_observer_can_be_created():
    observer = ScreenObserver()

    assert observer is not None


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Screen observer currently supports Windows only.",
)
def test_screen_size_is_positive():
    observer = ScreenObserver()

    width, height = observer.get_screen_size()

    assert width > 0
    assert height > 0


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Screen observer currently supports Windows only.",
)
def test_cursor_position_returns_coordinates():
    observer = ScreenObserver()

    x, y = observer.get_cursor_position()

    assert isinstance(x, int)
    assert isinstance(y, int)


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Screen observer currently supports Windows only.",
)
def test_snapshot_contains_screen_information():
    observer = ScreenObserver()

    snapshot = observer.snapshot()

    assert isinstance(snapshot, ScreenSnapshot)
    assert snapshot.width > 0
    assert snapshot.height > 0
    assert isinstance(snapshot.cursor_x, int)
    assert isinstance(snapshot.cursor_y, int)
    assert snapshot.platform == "Windows"


@pytest.mark.skipif(
    platform.system() != "Windows",
    reason="Screen observer currently supports Windows only.",
)
def test_snapshot_dictionary():
    observer = ScreenObserver()

    data = observer.as_dict()

    assert data["width"] > 0
    assert data["height"] > 0
    assert isinstance(data["cursor_x"], int)
    assert isinstance(data["cursor_y"], int)
    assert data["platform"] == "Windows"