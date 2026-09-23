import sys
from pathlib import Path
from typing import Optional


WINDOWS_VENV_PATHS = (
    Path(".venv") / "Scripts" / "python.exe",
    Path("venv") / "Scripts" / "python.exe",
)

POSIX_VENV_PATHS = (
    Path(".venv") / "bin" / "python",
    Path("venv") / "bin" / "python",
)


def inspect_interpreter():
    executable = Path(sys.executable).resolve()

    prefix = Path(sys.prefix).resolve()

    base_prefix = Path(
        getattr(sys, "base_prefix", sys.prefix)
    ).resolve()

    is_virtual_environment = prefix != base_prefix

    return {
        "executable": str(executable),
        "version": sys.version.split()[0],
        "prefix": str(prefix),
        "base_prefix": str(base_prefix),
        "virtual_environment": is_virtual_environment,
    }


def find_project_interpreter(
    project_root: str | Path,
) -> Optional[str]:
    """
    Find the Python interpreter belonging to a project.

    Preference order:

        .venv
        venv
        current FixPilot interpreter

    The function only discovers an interpreter.
    It never creates or modifies an environment.
    """

    root = Path(project_root).resolve()

    if not root.exists():
        return None

    if not root.is_dir():
        return None

    candidates = []

    if sys.platform == "win32":
        candidates.extend(
            root / relative
            for relative in WINDOWS_VENV_PATHS
        )
    else:
        candidates.extend(
            root / relative
            for relative in POSIX_VENV_PATHS
        )

    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue

        if candidate.is_file():
            return str(candidate)

    current = Path(sys.executable).resolve()

    if current.is_file():
        return str(current)

    return None


def interpreter_matches(expected_executable):
    if not expected_executable:
        return False

    current = Path(sys.executable).resolve()

    try:
        expected = Path(expected_executable).resolve()
    except (OSError, ValueError):
        return False

    return current == expected