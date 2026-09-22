import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def _run_command(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            shell=False,
        )

        return {
            "ok": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
        }

    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "ok": False,
            "stdout": "",
            "stderr": str(exc),
            "returncode": None,
        }


def detect_python():
    python_executable = Path(sys.executable).resolve()

    version = platform.python_version()

    pip_result = _run_command(
        [str(python_executable), "-m", "pip", "--version"]
    )

    pip_version = None

    if pip_result["ok"]:
        pip_version = pip_result["stdout"]

    return {
        "available": True,
        "version": version,
        "executable": str(python_executable),
        "pip": pip_version,
    }


def detect_virtual_environment():
    prefix = Path(sys.prefix).resolve()
    base_prefix = Path(getattr(sys, "base_prefix", sys.prefix)).resolve()

    active = prefix != base_prefix

    virtual_env = os.environ.get("VIRTUAL_ENV")

    if virtual_env:
        path = Path(virtual_env).resolve()
    elif active:
        path = prefix
    else:
        path = None

    return {
        "active": active,
        "path": str(path) if path else None,
        "name": path.name if path else None,
    }


def detect_node():
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")

    node_version = None
    npm_version = None

    if node_path:
        result = _run_command([node_path, "--version"])

        if result["ok"]:
            node_version = result["stdout"]

    if npm_path:
        result = _run_command([npm_path, "--version"])

        if result["ok"]:
            npm_version = result["stdout"]

    return {
        "available": bool(node_path),
        "node": node_path,
        "node_version": node_version,
        "npm": npm_path,
        "npm_version": npm_version,
    }


def detect_environment(project_root="."):
    root = Path(project_root).resolve()

    return {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "architecture": platform.machine(),
        },
        "project": {
            "root": str(root),
            "exists": root.exists(),
        },
        "python": detect_python(),
        "virtual_environment": detect_virtual_environment(),
        "node": detect_node(),
    }