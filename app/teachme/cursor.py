import ctypes
from ctypes import wintypes
import platform


def get_cursor_position():
    """Return the current pointer position without moving it."""
    if platform.system() != "Windows":
        return None

    point = wintypes.POINT()

    if ctypes.windll.user32.GetCursorPos(ctypes.byref(point)):
        return {"x": point.x, "y": point.y}

    return None