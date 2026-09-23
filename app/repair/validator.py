import re
from pathlib import Path


# Actions that FixPilot is currently allowed to execute.
#
# IMPORTANT:
# The validator only approves known structured actions.
# It never accepts arbitrary shell commands.
ALLOWED_ACTIONS = {
    "pip_install",
    "npm_install",
    "declare_dependency",
    "inspect_port",
    "inspect_path",
    "verify_import",
    "verify_environment",
}


# Conservative package-name validation.
#
# Python:
#   flask
#   requests
#   python-dotenv
#   beautifulsoup4
#
# Node:
#   express
#   @scope/package
PACKAGE_PATTERN = re.compile(
    r"^(?:@[A-Za-z0-9._-]+/)?[A-Za-z0-9._-]+$"
)


def _valid_package(package):
    """
    Validate a package name without allowing shell syntax.

    Examples rejected:
        flask && whoami
        flask;del something
        flask | powershell
        $(command)
        `command`
    """

    if not isinstance(package, str):
        return False

    package = package.strip()

    if not package:
        return False

    if len(package) > 214:
        return False

    return bool(PACKAGE_PATTERN.fullmatch(package))


def _valid_port(port):
    """
    Validate a TCP port number.
    """

    return (
        isinstance(port, int)
        and not isinstance(port, bool)
        and 1 <= port <= 65535
    )


def _validate_project_root(project_root):
    """
    Validate that the supplied project root exists
    and is a directory.
    """

    if project_root is None:
        return False

    try:
        path = Path(project_root).resolve()
    except (OSError, RuntimeError, TypeError):
        return False

    return path.exists() and path.is_dir()


def validate_repair_plan(plan, project_root="."):
    """
    Validate a structured FixPilot repair plan.

    Returns:

        {
            "allowed": True/False,
            "reason": "...",
            "action": "...",
            "package": "...",
            "risk": "LOW"
        }

    This validator does NOT execute anything.
    """

    if not isinstance(plan, dict):
        return {
            "allowed": False,
            "reason": "Repair plan must be a dictionary.",
            "action": None,
            "package": None,
            "risk": "UNKNOWN",
        }

    action = plan.get("action")

    if not isinstance(action, str):
        return {
            "allowed": False,
            "reason": "Repair plan does not contain a valid action.",
            "action": action,
            "package": None,
            "risk": "UNKNOWN",
        }

    action = action.strip()

    if action not in ALLOWED_ACTIONS:
        return {
            "allowed": False,
            "reason": f"Action '{action}' is not allowed.",
            "action": action,
            "package": plan.get("package"),
            "risk": "HIGH",
        }

    # All filesystem/project-aware actions require
    # a real project directory.
    if not _validate_project_root(project_root):
        return {
            "allowed": False,
            "reason": "Project root does not exist or is not a directory.",
            "action": action,
            "package": plan.get("package"),
            "risk": "HIGH",
        }

    package_actions = {
        "pip_install",
        "npm_install",
        "declare_dependency",
        "verify_import",
    }

    if action in package_actions:
        package = plan.get("package")

        if not _valid_package(package):
            return {
                "allowed": False,
                "reason": (
                    "Package name is invalid or contains "
                    "unsafe shell characters."
                ),
                "action": action,
                "package": package,
                "risk": "HIGH",
            }

    if action == "inspect_port":
        port = plan.get("port")

        if not _valid_port(port):
            return {
                "allowed": False,
                "reason": "Port must be an integer between 1 and 65535.",
                "action": action,
                "package": None,
                "risk": "HIGH",
            }

    # Explicitly reject arbitrary command fields.
    #
    # A repair plan should never be able to sneak a raw
    # command into the executor.
    forbidden_fields = {
        "command",
        "cmd",
        "shell",
        "shell_command",
        "powershell",
        "script",
        "exec",
        "executable",
    }

    present_forbidden = forbidden_fields.intersection(plan.keys())

    if present_forbidden:
        return {
            "allowed": False,
            "reason": (
                "Repair plan contains forbidden execution fields: "
                + ", ".join(sorted(present_forbidden))
            ),
            "action": action,
            "package": plan.get("package"),
            "risk": "HIGH",
        }

    return {
        "allowed": True,
        "reason": "Repair plan passed safety validation.",
        "action": action,
        "package": plan.get("package"),
        "risk": plan.get("risk", "LOW"),
    }


def is_repair_plan_safe(plan, project_root="."):
    """
    Convenience boolean wrapper.
    """

    result = validate_repair_plan(
        plan,
        project_root,
    )

    return result["allowed"]