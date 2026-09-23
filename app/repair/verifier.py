import importlib.util
import shutil
import subprocess
from pathlib import Path


def _run_original_command(command, cwd=None):
    """
    Re-run the original failing command.

    This preserves the existing V0.9 verification behavior.
    """

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
    Verify that a Python module can be discovered/imported.
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
        }

    except (ImportError, ModuleNotFoundError, ValueError) as exc:
        return {
            "success": False,
            "message": (
                f"Could not verify Python module "
                f"'{module_name}': {exc}"
            ),
            "module": module_name,
        }


def verify_python_import_runtime(module_name):
    """
    Actually execute a Python import in a separate process.

    find_spec() can confirm that a module exists, but a real
    import catches cases where the package exists but cannot
    actually load.
    """

    if not isinstance(module_name, str) or not module_name.strip():
        return {
            "success": False,
            "message": "Python module name is missing.",
        }

    module_name = module_name.strip()

    try:
        result = subprocess.run(
            [
                "python",
                "-c",
                f"import {module_name}",
            ],
            capture_output=True,
            text=True,
            timeout=30,
            shell=False,
        )

        output = (
            (result.stdout or "")
            + (result.stderr or "")
        ).strip()

        if result.returncode == 0:
            return {
                "success": True,
                "message": (
                    f"Python import verification passed "
                    f"for '{module_name}'."
                ),
                "module": module_name,
            }

        return {
            "success": False,
            "message": (
                f"Python import verification failed "
                f"for '{module_name}'."
            ),
            "module": module_name,
            "output": output[-3000:],
        }

    except Exception as exc:
        return {
            "success": False,
            "message": (
                f"Python runtime verification failed: {exc}"
            ),
            "module": module_name,
        }


def verify_node_module(package_name, cwd=None):
    """
    Verify that a Node package can be resolved from the project.
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
                (
                    "require.resolve("
                    f"{package_name!r}"
                    ")"
                ),
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

    except Exception as exc:
        return {
            "success": False,
            "message": (
                f"Node module verification failed: {exc}"
            ),
            "package": package_name,
        }


def verify_environment():
    """
    Verify that the basic Python and Node runtimes are available.
    """

    python_available = shutil.which("python") is not None
    node_available = shutil.which("node") is not None

    checks = {
        "python": python_available,
        "node": node_available,
    }

    if python_available or node_available:
        return {
            "success": True,
            "message": "Development environment is partially available.",
            "checks": checks,
        }

    return {
        "success": False,
        "message": "Python and Node.js were not found on PATH.",
        "checks": checks,
    }


def verify_plan(
    plan,
    results,
    cwd=None,
    original_command=None,
):
    """
    Verify a completed repair plan.

    This keeps the original V0.9 API while adding
    V1.3 structured verification.
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

            verification = verify_python_import(package)
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

            verification = verify_python_import(package)
            verification_results.append(verification)

            if not verification["success"]:
                unresolved.append(
                    verification["message"]
                )

        elif action == "verify_environment":
            verification = verify_environment()
            verification_results.append(verification)

            if not verification["success"]:
                unresolved.append(
                    verification["message"]
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

    # ---------------------------------------------------------
    # Re-run original command when supplied.
    # ---------------------------------------------------------

    command_result = _run_original_command(
        original_command,
        cwd,
    )

    if command_result and command_result["returncode"] != 0:
        unresolved.append(
            "Original command still exits with "
            f"code {command_result['returncode']}."
        )

    # ---------------------------------------------------------
    # Final result.
    # ---------------------------------------------------------

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