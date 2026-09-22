import sys
from pathlib import Path


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


def interpreter_matches(expected_executable):
    if not expected_executable:
        return False

    current = Path(sys.executable).resolve()

    try:
        expected = Path(expected_executable).resolve()
    except (OSError, ValueError):
        return False

    return current == expected