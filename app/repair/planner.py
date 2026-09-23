import re

from app.agent.conflict_reasoner import analyze_dependency_conflict
from app.agent.root_cause import analyze_root_cause


def _extract_python_package(error):
    """Extract the top-level Python package from a ModuleNotFoundError."""

    match = re.search(
        r"No module named ['\"]?([A-Za-z0-9_.-]+)['\"]?",
        error,
        re.IGNORECASE,
    )

    if not match:
        return None

    return match.group(1).split(".")[0]


def _extract_node_package(error):
    """Extract a Node.js package from MODULE_NOT_FOUND errors."""

    match = re.search(
        r"(?:Cannot find module|Cannot find package)\s+['\"]([^'\"]+)['\"]",
        error,
        re.IGNORECASE,
    )

    if not match:
        return None

    package = match.group(1)

    # Ignore local paths.
    if (
        package.startswith(".")
        or package.startswith("/")
        or "\\" in package
    ):
        return None

    # Preserve scoped packages such as @scope/package.
    if package.startswith("@"):
        parts = package.split("/")

        if len(parts) >= 2:
            return "/".join(parts[:2])

    return package.split("/")[0]


def _extract_port(error):
    """
    Extract a TCP port from common EADDRINUSE errors.

    Examples:
        EADDRINUSE: address already in use :::3000
        listen EADDRINUSE: address already in use 127.0.0.1:8000
        EADDRINUSE port 3000
    """

    patterns = [
        r"address already in use\s+.*?:(\d+)",
        r"EADDRINUSE.*?:(\d+)",
        r"\bport\s+(\d+)\b",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            error,
            re.IGNORECASE,
        )

        if match:
            try:
                return int(match.group(1))
            except (TypeError, ValueError):
                pass

    return None


def build_error_repair_plan(category, error):
    """
    Original category-based repair planner.

    This function only creates a repair plan.
    It never executes the repair.
    """

    plans = []

    if category == "python_missing_module":
        package = _extract_python_package(error)

        if package:
            plans.append(
                {
                    "action": "pip_install",
                    "package": package,
                    "risk": "LOW",
                    "reason": (
                        f"Python dependency '{package}' "
                        "appears to be missing."
                    ),
                }
            )

    elif category == "node_missing_module":
        package = _extract_node_package(error)

        if package:
            plans.append(
                {
                    "action": "npm_install",
                    "package": package,
                    "risk": "LOW",
                    "reason": (
                        f"Node dependency '{package}' "
                        "appears to be missing."
                    ),
                }
            )

    elif category == "port_in_use":
        port = _extract_port(error)

        plan = {
            "action": "inspect_port",
            "risk": "LOW",
            "reason": (
                "Another process may already be using "
                "the requested port."
            ),
        }

        if port is not None:
            plan["port"] = port

        plans.append(plan)

    elif category == "command_not_found":
        plans.append(
            {
                "action": "inspect_path",
                "risk": "LOW",
                "reason": (
                    "The requested command could not be "
                    "resolved from PATH."
                ),
            }
        )

    return plans


def _dependency_from_conflict(conflict):
    """Convert conflict analysis into root-cause dependency input."""

    if not conflict:
        return None

    installed = conflict.get("installed", False)
    declared = conflict.get("declared", False)

    if isinstance(installed, dict):
        installed = installed.get("installed", False)

    return {
        "installed": bool(installed),
        "declared": bool(declared),
        "installed_version": conflict.get("installed_version"),
        "declaration": conflict.get("declaration"),
    }


def _build_reasoned_plan_from_root_cause(
    root_cause,
    package,
):
    """
    Convert root-cause analysis into a structured repair plan.

    No command is executed here.
    """

    cause_code = root_cause.get("cause_code")
    confidence = root_cause.get("confidence", 0.0)
    evidence = root_cause.get("evidence", [])
    dependency_state = root_cause.get("dependency_state")
    reason = root_cause.get("root_cause")

    # ---------------------------------------------------------
    # Package installed but not declared
    # ---------------------------------------------------------

    if cause_code == "dependency_not_declared":
        return {
            "action": "declare_dependency",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Package declared but not installed
    # ---------------------------------------------------------

    if cause_code == "dependency_not_installed":
        return {
            "action": "pip_install",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Package missing and undeclared
    # ---------------------------------------------------------

    if cause_code == "missing_dependency":
        return {
            "action": "declare_dependency",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Package installed + declared but import failed
    #
    # Existing V1.1 behavior expects verify_import.
    # ---------------------------------------------------------

    if cause_code == "environment_mismatch":
        return {
            "action": "verify_import",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Python dependency state unknown
    # ---------------------------------------------------------

    if cause_code == "python_dependency_unknown":
        return {
            "action": "verify_environment",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Node package installed but not declared
    # ---------------------------------------------------------

    if cause_code == "node_dependency_not_declared":
        return {
            "action": "npm_install",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Node package declared but not installed
    # ---------------------------------------------------------

    if cause_code == "node_dependency_not_installed":
        return {
            "action": "npm_install",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Node package missing
    # ---------------------------------------------------------

    if cause_code == "node_missing_dependency":
        return {
            "action": "npm_install",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    # ---------------------------------------------------------
    # Node environment mismatch
    # ---------------------------------------------------------

    if cause_code == "node_environment_mismatch":
        return {
            "action": "verify_environment",
            "package": package,
            "risk": "LOW",
            "reason": reason,
            "cause_code": cause_code,
            "confidence": confidence,
            "evidence": evidence,
            "dependency_state": dependency_state,
        }

    return None


def build_reasoned_repair_plan(error, project_root="."):
    """
    Build a project-aware repair plan.

    Flow:

        Error
          ↓
        Diagnosis
          ↓
        Dependency conflict
          ↓
        Root-cause analysis
          ↓
        Structured repair plan

    This function does not execute repairs.
    """

    # Local import is intentional.
    #
    # diagnostician.py imports build_error_repair_plan
    # from this module. Keeping this import local prevents
    # the planner <-> diagnostician circular import.
    from app.agent.diagnostician import diagnose_error

    diagnosis = diagnose_error(error)

    category_code = diagnosis.get("category_code")
    fingerprint = diagnosis.get("fingerprint") or {}

    language = fingerprint.get("language")
    error_type = fingerprint.get("error_type")

    # ---------------------------------------------------------
    # Python ModuleNotFoundError
    # ---------------------------------------------------------

    if (
        language == "python"
        and error_type == "ModuleNotFoundError"
    ):
        module = (
            fingerprint.get("module")
            or fingerprint.get("package")
            or _extract_python_package(error)
        )

        if module:
            conflict = analyze_dependency_conflict(
                module,
                project_root,
            )

            dependency = _dependency_from_conflict(
                conflict
            )

            root_cause = analyze_root_cause(
                fingerprint,
                dependency=dependency,
                environment=conflict.get("environment"),
                conflict=conflict,
            )

            package = (
                root_cause.get("package")
                or conflict.get("package")
                or module
            )

            plan = _build_reasoned_plan_from_root_cause(
                root_cause,
                package,
            )

            if plan:
                return [plan]

            return build_error_repair_plan(
                category_code,
                error,
            )

    # ---------------------------------------------------------
    # Node MODULE_NOT_FOUND
    # ---------------------------------------------------------

    if (
        language == "node"
        and error_type == "MODULE_NOT_FOUND"
    ):
        package = (
            fingerprint.get("package")
            or fingerprint.get("module")
            or _extract_node_package(error)
        )

        if package:
            return build_error_repair_plan(
                category_code,
                error,
            )

    # ---------------------------------------------------------
    # Port conflict
    # ---------------------------------------------------------

    if error_type == "EADDRINUSE":
        return build_error_repair_plan(
            category_code,
            error,
        )

    # ---------------------------------------------------------
    # Command not found
    # ---------------------------------------------------------

    if category_code == "command_not_found":
        return build_error_repair_plan(
            category_code,
            error,
        )

    # ---------------------------------------------------------
    # Final fallback
    # ---------------------------------------------------------

    return build_error_repair_plan(
        category_code,
        error,
    )