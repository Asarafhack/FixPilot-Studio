from __future__ import annotations

import ctypes
import platform
from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenSnapshot:
    width: int
    height: int
    cursor_x: int
    cursor_y: int
    platform: str


class ScreenObserver:
    """Read-only Windows screen observer.

    This component only reads screen geometry and cursor position.
    It never moves the cursor, clicks, types, or launches applications.
    """

    def __init__(self):
        self._user32 = None

        if platform.system() == "Windows":
            self._user32 = ctypes.windll.user32

    def get_screen_size(self) -> tuple[int, int]:
        if self._user32 is None:
            raise RuntimeError(
                "ScreenObserver currently supports Windows only."
            )

        width = int(self._user32.GetSystemMetrics(0))
        height = int(self._user32.GetSystemMetrics(1))

        return width, height

    def get_cursor_position(self) -> tuple[int, int]:
        if self._user32 is None:
            raise RuntimeError(
                "ScreenObserver currently supports Windows only."
            )

        point = ctypes.wintypes.POINT()

        if not self._user32.GetCursorPos(ctypes.byref(point)):
            raise RuntimeError("Unable to read cursor position.")

        return int(point.x), int(point.y)

    def snapshot(self) -> ScreenSnapshot:
        width, height = self.get_screen_size()
        cursor_x, cursor_y = self.get_cursor_position()

        return ScreenSnapshot(
            width=width,
            height=height,
            cursor_x=cursor_x,
            cursor_y=cursor_y,
            platform=platform.system(),
        )

    def as_dict(self) -> dict[str, int | str]:
        snapshot = self.snapshot()

        return {
            "width": snapshot.width,
            "height": snapshot.height,
            "cursor_x": snapshot.cursor_x,
            "cursor_y": snapshot.cursor_y,
            "platform": snapshot.platform,
        }