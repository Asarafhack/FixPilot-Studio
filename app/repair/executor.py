import json
import subprocess
import sys
import time
from pathlib import Path

from app.repair.storage import logs_dir
from app.repair.validator import validate_repair_plan


LOG_DIR = logs_dir()
LOG_FILE = LOG_DIR / "repair_audit.jsonl"


def _audit(event, payload):
    """
    Write one structured repair event to the audit log.
    """

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": time.time(),
        "event": event,
        **payload,
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _run(command, cwd=None):
    """
    Execute a fixed argument list.

    shell=False is mandatory so the command cannot be
    interpreted by cmd.exe or PowerShell.
    """

    _audit(
        "command_started",
        {
            "command": command,
            "cwd": str(cwd or Path.cwd()),
        },
    )

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=120,
            shell=False,
            cwd=str(cwd) if cwd else None,
        )

        output = (result.stdout or "") + (result.stderr or "")

        _audit(
            "command_finished",
            {
                "command": command,
                "returncode": result.returncode,
                "output_tail": output[-3000:],
            },
        )

        return result.returncode == 0, output.strip()

    except subprocess.TimeoutExpired:
        _audit(
            "command_timeout",
            {
                "command": command,
            },
        )

        return False, "Repair command timed out."

    except OSError as exc:
        _audit(
            "command_error",
            {
                "command": command,
                "error": str(exc),
            },
        )

        return False, f"Could not execute repair: {exc}"


def execute_plan(plan, cwd=None):
    """
    Execute a structured FixPilot repair plan.

    Execution pipeline:

        Repair Plan
             ↓
        Safety Validator
             ↓
        Fixed argument list
             ↓
        subprocess(shell=False)

    The executor never accepts arbitrary shell commands.
    """

    if not isinstance(plan, dict):
        _audit(
            "repair_blocked",
            {
                "reason": "invalid_plan",
            },
        )

        return {
            "success": False,
            "message": "Repair plan must be a dictionary.",
        }

    project_root = cwd or Path.cwd()

    # ---------------------------------------------------------
    # STEP 1: SAFETY VALIDATION
    # ---------------------------------------------------------

    validation = validate_repair_plan(
        plan,
        project_root,
    )

    _audit(
        "repair_validation",
        {
            "allowed": validation["allowed"],
            "action": validation.get("action"),
            "package": validation.get("package"),
            "risk": validation.get("risk"),
            "reason": validation.get("reason"),
        },
    )

    if not validation["allowed"]:
        _audit(
            "repair_blocked",
            {
                "reason": validation["reason"],
                "action": plan.get("action"),
                "package": plan.get("package"),
            },
        )

        return {
            "success": False,
            "message": (
                "Repair blocked by safety validator: "
                + validation["reason"]
            ),
            "blocked": True,
            "validation": validation,
        }

    action = plan.get("action")

    # ---------------------------------------------------------
    # STEP 2: PYTHON PACKAGE INSTALL
    # ---------------------------------------------------------

    if action == "pip_install":
        package = plan["package"]

        ok, output = _run(
            [
                sys.executable,
                "-m",
                "pip",
                "install",
                package,
            ],
            cwd=cwd,
        )

        return {
            "success": ok,
            "blocked": False,
            "action": action,
            "package": package,
            "message": (
                f"$ {sys.executable} -m pip install {package}\n"
                f"{output}"
            ),
        }

    # ---------------------------------------------------------
    # STEP 3: NODE PACKAGE INSTALL
    # ---------------------------------------------------------

    if action == "npm_install":
        package = plan["package"]

        ok, output = _run(
            [
                "npm",
                "install",
                package,
            ],
            cwd=cwd,
        )

        return {
            "success": ok,
            "blocked": False,
            "action": action,
            "package": package,
            "message": (
                f"$ npm install {package}\n"
                f"{output}"
            ),
        }

    # ---------------------------------------------------------
    # STEP 4: DECLARE DEPENDENCY
    # ---------------------------------------------------------

    if action == "declare_dependency":
        package = plan["package"]

        _audit(
            "guidance_only",
            {
                "action": action,
                "package": package,
            },
        )

        return {
            "success": True,
            "blocked": False,
            "action": action,
            "package": package,
            "message": (
                f"Package '{package}' is not declared by the project. "
                "Dependency declaration is required before automatic "
                "repair can continue."
            ),
        }

    # ---------------------------------------------------------
    # STEP 5: VERIFY IMPORT
    # ---------------------------------------------------------

    if action == "verify_import":
        package = plan["package"]

        ok, output = _run(
            [
                sys.executable,
                "-c",
                (
                    "import importlib.util; "
                    f"spec = importlib.util.find_spec({package!r}); "
                    "raise SystemExit(0 if spec else 1)"
                ),
            ],
            cwd=cwd,
        )

        if ok:
            message = (
                f"Import verification passed for '{package}'."
            )
        else:
            message = (
                f"Import verification failed for '{package}'.\n"
                f"{output}"
            )

        return {
            "success": ok,
            "blocked": False,
            "action": action,
            "package": package,
            "message": message,
        }

    # ---------------------------------------------------------
    # STEP 6: VERIFY ENVIRONMENT
    # ---------------------------------------------------------

    if action == "verify_environment":
        _audit(
            "guidance_only",
            {
                "action": action,
            },
        )

        return {
            "success": True,
            "blocked": False,
            "action": action,
            "message": (
                "Environment verification requested. "
                "No environment modification was made."
            ),
        }

    # ---------------------------------------------------------
    # STEP 7: INSPECT PORT
    # ---------------------------------------------------------

    if action == "inspect_port":
        port = plan["port"]

        _audit(
            "guidance_only",
            {
                "action": action,
                "port": port,
            },
        )

        return {
            "success": True,
            "blocked": False,
            "action": action,
            "port": port,
            "message": (
                f"Port {port} is busy. "
                "No process was terminated."
            ),
        }

    # ---------------------------------------------------------
    # STEP 8: INSPECT PATH
    # ---------------------------------------------------------

    if action == "inspect_path":
        _audit(
            "guidance_only",
            {
                "action": action,
            },
        )

        return {
            "success": True,
            "blocked": False,
            "action": action,
            "message": (
                "PATH inspection requested. "
                "No PATH modification was made."
            ),
        }

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    _audit(
        "repair_blocked",
        {
            "reason": "unsupported_action_after_validation",
            "action": action,
        },
    )

    return {
        "success": False,
        "blocked": True,
        "action": action,
        "message": "Unsupported repair action blocked.",
    }