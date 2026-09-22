import importlib.util
import shutil
from pathlib import Path

def _run_original_command(command, cwd=None):
    import subprocess
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
            "output": ((result.stdout or "") + (result.stderr or ""))[-5000:]
        }
    except Exception as exc:
        return {"returncode": -1, "output": str(exc)}

def verify_plan(plan, results, cwd=None, original_command=None):
    if not plan:
        return {"success": False, "message": "No repair plan is available."}

    unresolved = []

    for item in plan:
        action = item.get("action")

        if action == "pip_install":
            package = item.get("package", "")
            if importlib.util.find_spec(package) is None:
                unresolved.append(f"Python module '{package}' is still unavailable.")

        elif action == "npm_install":
            if not shutil.which("npm"):
                unresolved.append("npm is unavailable, so Node verification cannot run.")

        elif action == "show_port_guidance":
            unresolved.append("Port guidance was shown; no process was terminated.")

    command_result = _run_original_command(original_command, cwd)
    if command_result and command_result["returncode"] != 0:
        unresolved.append(
            f"Original command still exits with code {command_result['returncode']}."
        )

    if unresolved:
        return {
            "success": False,
            "message": "Attention remains:\n- " + "\n- ".join(unresolved),
            "command_result": command_result,
        }

    return {
        "success": True,
        "message": "Repair verification passed.",
        "command_result": command_result,
    }
