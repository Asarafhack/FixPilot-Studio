import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path

from app.context.interpreter import find_project_interpreter


def _run_original_command(command, cwd=None):
    if not command:
        return None

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            shell=False,
            cwd=str(cwd) if cwd else None,
        )

        return {
            "returncode": result.returncode,
            "output": (
                (result.stdout or "")
                + (result.stderr or "")
            )[-5000:],
        }

    except Exception as exc:
        return {
            "returncode": -1,
            "output": str(exc),
        }


def verify_python_import(module_name):
    """
    Verify that a Python module can be discovered by the
    current FixPilot Python interpreter.

    This is a lightweight inspection check.
    For project-aware verification, use
    verify_python_import_runtime().
    """

    if not isinstance(module_name, str) or not module_name.strip():
        return {
            "success": False,
            "message": "Python module name is missing.",
        }

    module_name = module_name.strip()

    try:
        spec = importlib.util.find_spec(module_name)

        if spec is None:
            return {
                "success": False,
                "message": (
                    f"Python module '{module_name}' "
                    "is still unavailable."
                ),
                "module": module_name,
            }

        return {
            "success": True,
            "message": (
                f"Python module '{module_name}' "
                "is available."
            ),
            "module": module_name,
            "interpreter": sys.executable,
        }

    except (
        ImportError,
        ModuleNotFoundError,
        ValueError,
    ) as exc:
        return {
            "success": False,
            "message": (
                f"Could not verify Python module "
                f"'{module_name}': {exc}"
            ),
            "module": module_name,
        }


def verify_python_import_runtime(
    module_name,
    project_root=None,
):
    """
    Actually import a Python module using the interpreter
    belonging to the target project.

    If the project contains:

        .venv\\Scripts\\python.exe

    or:

        venv\\Scripts\\python.exe

    that interpreter is preferred.

    This prevents FixPilot from accidentally validating a
    globally installed package when the application itself
    runs inside a project virtual environment.
    """

    if not isinstance(module_name, str) or not module_name.strip():
        return {
            "success": False,
            "message": "Python module name is missing.",
        }

    module_name = module_name.strip()

    project_path = (
        Path(project_root).resolve()
        if project_root
        else Path.cwd().resolve()
    )

    interpreter = find_project_interpreter(
        project_path
    )

    if not interpreter:
        return {
            "success": False,
            "message": (
                "Could not determine the Python interpreter "
                "for the target project."
            ),
            "module": module_name,
            "interpreter": None,
            "project_root": str(project_path),
        }

    try:
        result = subprocess.run(
            [
                interpreter,
                "-c",
                f"import {module_name}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
            cwd=str(project_path),
        )

        output = (
            (result.stdout or "")
            + (result.stderr or "")
        ).strip()

        if result.returncode == 0:
            return {
                "success": True,
                "message": (
                    f"Python runtime import verification "
                    f"passed for '{module_name}'."
                ),
                "module": module_name,
                "interpreter": interpreter,
                "project_root": str(project_path),
            }

        return {
            "success": False,
            "message": (
                f"Python runtime import verification "
                f"failed for '{module_name}'."
            ),
            "module": module_name,
            "interpreter": interpreter,
            "project_root": str(project_path),
            "output": output[-3000:],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": (
                f"Python runtime import verification "
                f"timed out for '{module_name}'."
            ),
            "module": module_name,
            "interpreter": interpreter,
            "project_root": str(project_path),
        }

    except OSError as exc:
        return {
            "success": False,
            "message": (
                f"Could not execute project Python "
                f"interpreter: {exc}"
            ),
            "module": module_name,
            "interpreter": interpreter,
            "project_root": str(project_path),
        }

    except Exception as exc:
        return {
            "success": False,
            "message": (
                f"Python runtime verification failed: {exc}"
            ),
            "module": module_name,
            "interpreter": interpreter,
            "project_root": str(project_path),
        }


def verify_node_module(package_name, cwd=None):
    """
    Verify that a Node package can be resolved from
    the target project.
    """

    if not isinstance(package_name, str) or not package_name.strip():
        return {
            "success": False,
            "message": "Node package name is missing.",
        }

    package_name = package_name.strip()

    if not shutil.which("node"):
        return {
            "success": False,
            "message": "Node.js is unavailable.",
            "package": package_name,
        }

    try:
        result = subprocess.run(
            [
                "node",
                "-e",
                f"require.resolve({package_name!r})",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
            cwd=str(cwd) if cwd else None,
        )

        output = (
            (result.stdout or "")
            + (result.stderr or "")
        ).strip()

        if result.returncode == 0:
            return {
                "success": True,
                "message": (
                    f"Node module '{package_name}' "
                    "is available."
                ),
                "package": package_name,
            }

        return {
            "success": False,
            "message": (
                f"Node module '{package_name}' "
                "is unavailable."
            ),
            "package": package_name,
            "output": output[-3000:],
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "message": (
                f"Node module verification timed out "
                f"for '{package_name}'."
            ),
            "package": package_name,
        }

    except OSError as exc:
        return {
            "success": False,
            "message": (
                f"Node module verification failed: {exc}"
            ),
            "package": package_name,
        }

    except Exception as exc:
        return {
            "success": False,
            "message": (
                f"Node module verification failed: {exc}"
            ),
            "package": package_name,
        }


def verify_environment(project_root=None):
    """
    Verify the development runtimes available to FixPilot
    and identify the interpreter used by the target project.
    """

    project_interpreter = find_project_interpreter(
        project_root or Path.cwd()
    )

    python_available = bool(project_interpreter)
    node_available = shutil.which("node") is not None

    checks = {
        "python": python_available,
        "node": node_available,
    }

    return {
        "success": python_available or node_available,
        "message": (
            "Development environment is partially available."
            if python_available or node_available
            else "Python and Node.js are unavailable."
        ),
        "checks": checks,
        "python_executable": project_interpreter,
        "fixpilot_python_executable": sys.executable,
    }


def verify_plan(
    plan,
    results,
    cwd=None,
    original_command=None,
):
    """
    Verify a completed repair plan.

    Python verification is performed using the target
    project's interpreter, not FixPilot's own interpreter.
    """

    if not plan:
        return {
            "success": False,
            "message": "No repair plan is available.",
        }

    unresolved = []
    verification_results = []

    for item in plan:
        action = item.get("action")

        if action == "pip_install":
            package = item.get("package", "")

            verification = verify_python_import_runtime(
                package,
                project_root=cwd,
            )

            verification_results.append(verification)

            if not verification["success"]:
                unresolved.append(
                    verification["message"]
                )

        elif action == "npm_install":
            package = item.get("package", "")

            verification = verify_node_module(
                package,
                cwd=cwd,
            )

            verification_results.append(verification)

            if not verification["success"]:
                unresolved.append(
                    verification["message"]
                )

        elif action == "verify_import":
            package = item.get("package", "")

            verification = verify_python_import_runtime(
                package,
                project_root=cwd,
            )

            verification_results.append(verification)

            if not verification["success"]:
                unresolved.append(
                    verification["message"]
                )

        elif action == "verify_environment":
            verification = verify_environment(
                project_root=cwd,
            )

            verification_results.append(verification)

            if not verification["success"]:
                unresolved.append(
                    verification["message"]
                )

        elif action == "declare_dependency":
            verification_results.append(
                {
                    "success": True,
                    "message": (
                        "Dependency declaration guidance "
                        "was processed."
                    ),
                    "action": action,
                    "package": item.get("package", ""),
                }
            )

        elif action in {
            "show_port_guidance",
            "inspect_port",
        }:
            unresolved.append(
                "Port guidance was shown; "
                "no process was terminated."
            )

        elif action in {
            "show_path_guidance",
            "inspect_path",
        }:
            unresolved.append(
                "PATH guidance was provided; "
                "no PATH modification was made."
            )

    command_result = _run_original_command(
        original_command,
        cwd,
    )

    if command_result and command_result["returncode"] != 0:
        unresolved.append(
            "Original command still exits with "
            f"code {command_result['returncode']}."
        )

    if unresolved:
        return {
            "success": False,
            "message": (
                "Attention remains:\n- "
                + "\n- ".join(unresolved)
            ),
            "command_result": command_result,
            "verification_results": verification_results,
        }

    return {
        "success": True,
        "message": "Repair verification passed.",
        "command_result": command_result,
        "verification_results": verification_results,
    }