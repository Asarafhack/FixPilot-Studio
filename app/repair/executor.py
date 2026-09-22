import json
import re
import subprocess
import sys
import time
from pathlib import Path
from app.repair.storage import logs_dir

SAFE_PACKAGE = re.compile(r"^[A-Za-z0-9_.-]+$")
LOG_DIR = logs_dir()
LOG_FILE = LOG_DIR / "repair_audit.jsonl"

def _audit(event, payload):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": time.time(),
        "event": event,
        **payload,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

def _run(command, cwd=None):
    _audit("command_started", {"command": command, "cwd": str(cwd or Path.cwd())})
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
        _audit("command_finished", {
            "command": command,
            "returncode": result.returncode,
            "output_tail": output[-3000:],
        })
        return result.returncode == 0, output.strip()
    except subprocess.TimeoutExpired:
        _audit("command_timeout", {"command": command})
        return False, "Repair command timed out."
    except OSError as exc:
        _audit("command_error", {"command": command, "error": str(exc)})
        return False, f"Could not execute repair: {exc}"

def execute_plan(plan, cwd=None):
    action = plan.get("action")

    if action == "pip_install":
        package = plan.get("package", "")
        if not SAFE_PACKAGE.fullmatch(package):
            _audit("repair_blocked", {"reason": "unsafe_python_package", "package": package})
            return {"success": False, "message": "Blocked unsafe Python package name."}

        ok, output = _run(
            [sys.executable, "-m", "pip", "install", package],
            cwd=cwd,
        )
        return {
            "success": ok,
            "message": f"$ {sys.executable} -m pip install {package}\n{output}"
        }

    if action == "npm_install":
        package = plan.get("package", "")
        if not SAFE_PACKAGE.fullmatch(package):
            _audit("repair_blocked", {"reason": "unsafe_npm_package", "package": package})
            return {"success": False, "message": "Blocked unsafe npm package name."}

        ok, output = _run(["npm", "install", package], cwd=cwd)
        return {
            "success": ok,
            "message": f"$ npm install {package}\n{output}"
        }

    if action == "show_port_guidance":
        port = plan.get("port")
        _audit("guidance_only", {"action": action, "port": port})
        return {
            "success": True,
            "message": f"Port {port or 'unknown'} is busy. No process was terminated."
        }

    if action == "show_path_guidance":
        _audit("guidance_only", {"action": action})
        return {
            "success": True,
            "message": "No PATH modification was made. Inspect installation and PATH manually."
        }

    _audit("repair_blocked", {"reason": "unsupported_action", "action": action})
    return {"success": False, "message": "Unsupported repair action blocked."}
