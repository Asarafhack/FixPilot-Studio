import os
import platform
import shutil
import socket
import subprocess
import sys

TOOLS = [
    ("Python", "python", [sys.executable, "--version"]),
    ("Node.js", "node", ["node", "--version"]),
    ("npm", "npm", ["npm", "--version"]),
    ("Git", "git", ["git", "--version"]),
]

def _run_version(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=8, shell=False)
        return result.returncode, (result.stdout or result.stderr).strip()
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)

def check_tool(name, executable, command):
    path = shutil.which(executable)
    if not path:
        return {"name": name, "status": "MISSING",
                "message": f"{executable} was not found in PATH."}
    code, version = _run_version(command)
    return {
        "name": name,
        "status": "OK" if code == 0 else "ERROR",
        "message": f"Found at {path}" if code == 0 else f"Version check failed: {version}",
        "version": version
    }

def check_environment():
    return {
        "name": "PATH",
        "status": "OK" if os.environ.get("PATH") else "ERROR",
        "message": "Environment PATH is available." if os.environ.get("PATH")
                   else "PATH environment variable is empty."
    }

def check_system():
    return {
        "name": "Windows",
        "status": "OK" if platform.system() == "Windows" else "INFO",
        "message": f"Detected operating system: {platform.system()} {platform.release()}"
    }

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        used = sock.connect_ex(("127.0.0.1", port)) == 0
    finally:
        sock.close()
    return {"name": f"Port {port}",
            "status": "BUSY" if used else "FREE",
            "message": f"127.0.0.1:{port} is {'already in use' if used else 'available'}."}

def run_all_diagnostics():
    results = [check_system(), check_environment()]
    for name, executable, command in TOOLS:
        results.append(check_tool(name, executable, command))
    for port in (8000, 3000, 5173):
        results.append(check_port(port))
    return results
