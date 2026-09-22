import re


def _extract_python_package(error):
    """
    Extract the top-level Python import/package name from a
    ModuleNotFoundError message.
    """

    if not error:
        return None

    match = re.search(
        r"No module named\s+['\"]?([A-Za-z0-9_.-]+)['\"]?",
        error,
        re.I,
    )

    if not match:
        return None

    return match.group(1).split(".")[0]


def _extract_node_package(error):
    """
    Extract a Node.js package name from common module errors.
    """

    if not error:
        return None

    patterns = [
        r"Cannot find module\s+['\"]([^'\"]+)['\"]",
        r"Cannot find package\s+['\"]([^'\"]+)['\"]",
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            error,
            re.I,
        )

        if not match:
            continue

        package = match.group(1).strip()

        # Local files are not npm packages.
        if package.startswith("."):
            return None

        if package.startswith("/"):
            return None

        if package.startswith("@"):
            parts = package.split("/")

            if len(parts) >= 2:
                return "/".join(parts[:2])

        return package

    return None


def build_error_repair_plan(category, error):
    """
    Build a basic repair plan from a diagnosed error.

    This is the original V1.0-compatible planner API.

    Safety validation and actual command execution must happen
    downstream in the repair executor/validator.
    """

    if category == "python_missing_module":
        package = _extract_python_package(error)

        if not package:
            return []

        return [
            {
                "id": "python_missing_module",
                "title": f"Install Python package: {package}",
                "reason": (
                    "The active Python environment cannot import "
                    "the reported module."
                ),
                "action": "pip_install",
                "package": package,
                "preview": (
                    f"{package} will be installed with the active "
                    "Python interpreter."
                ),
                "risk": "LOW",
            }
        ]

    if category == "node_missing_module":
        package = _extract_node_package(error)

        if not package:
            return []

        return [
            {
                "id": "node_missing_module",
                "title": f"Install Node package: {package}",
                "reason": (
                    "The Node.js project cannot resolve the "
                    "reported module."
                ),
                "action": "npm_install",
                "package": package,
                "preview": (
                    f"{package} will be installed using the "
                    "project package manager."
                ),
                "risk": "LOW",
            }
        ]

    if category == "port_in_use":
        match = re.search(
            r"(?:port|:)\s*(\d{2,5})",
            error,
            re.I,
        )

        if not match:
            return []

        port = int(match.group(1))

        if port < 1 or port > 65535:
            return []

        return [
            {
                "id": "port_in_use",
                "title": f"Inspect process using port {port}",
                "reason": (
                    f"Another process is already using port {port}."
                ),
                "action": "inspect_port",
                "port": port,
                "preview": (
                    f"Identify the process currently listening "
                    f"on port {port} before taking further action."
                ),
                "risk": "LOW",
            }
        ]

    if category == "command_not_found":
        match = re.search(
            r"(?:'([^']+)'|\"([^\"]+)\"|^|\s)"
            r"([A-Za-z0-9_.-]+)"
            r"(?:\s+is not recognized|\s+not found)",
            error,
            re.I,
        )

        command = None

        if match:
            command = (
                match.group(1)
                or match.group(2)
                or match.group(3)
            )

        if not command:
            return []

        return [
            {
                "id": "command_not_found",
                "title": f"Inspect command: {command}",
                "reason": (
                    f"The command '{command}' is not available "
                    "in the current environment."
                ),
                "action": "inspect_path",
                "command": command,
                "preview": (
                    f"Check whether '{command}' is installed "
                    "and available through PATH."
                ),
                "risk": "LOW",
            }
        ]

    return []


def build_reasoned_repair_plan(error, project_root="."):
    """
    Build a repair plan using project-aware dependency reasoning.

    The reasoning layer decides whether the dependency should be:
    - verified
    - declared
    - installed
    - handled as an environment issue

    The actual repair executor remains responsible for
    safety validation and command execution.
    """

    from app.agent.diagnostician import diagnose_error
    from app.agent.conflict_reasoner import analyze_dependency_conflict

    diagnosis = diagnose_error(error)

    category_code = diagnosis["category_code"]

    if category_code != "python_missing_module":
        return build_error_repair_plan(
            category_code,
            error,
        )

    module = _extract_python_package(error)

    if not module:
        return build_error_repair_plan(
            category_code,
            error,
        )

    conflict = analyze_dependency_conflict(
        module,
        project_root,
    )

    status = conflict["status"]
    package = conflict["package"]

    # ---------------------------------------------------------
    # Package is installed and declared.
    # ---------------------------------------------------------
    if status == "healthy":
        return [
            {
                "id": "verify_import",
                "title": f"Verify Python import: {module}",
                "reason": (
                    f"{package} is installed and declared "
                    "by the project."
                ),
                "action": "verify_import",
                "package": package,
                "preview": (
                    f"Verify that {module} imports successfully "
                    "with the active Python interpreter."
                ),
                "risk": "LOW",
            }
        ]

    # ---------------------------------------------------------
    # Package is installed globally/environment-wise but the
    # project does not declare it.
    # ---------------------------------------------------------
    if status == "installed_not_declared":
        return [
            {
                "id": "declare_dependency",
                "title": f"Declare Python dependency: {package}",
                "reason": (
                    f"{package} is installed in the active "
                    "environment but is not declared by "
                    "the project."
                ),
                "action": "declare_dependency",
                "package": package,
                "preview": (
                    f"Add {package} to the project's dependency "
                    "configuration."
                ),
                "risk": "LOW",
            }
        ]

    # ---------------------------------------------------------
    # Package is declared but missing from the active environment.
    # ---------------------------------------------------------
    if status == "declared_not_installed":
        return [
            {
                "id": "python_missing_module",
                "title": f"Install Python package: {package}",
                "reason": (
                    f"{package} is declared by the project "
                    "but is not installed in the active "
                    "environment."
                ),
                "action": "pip_install",
                "package": package,
                "preview": (
                    f"{package} will be installed with the "
                    "active Python interpreter."
                ),
                "risk": "LOW",
            }
        ]

    # ---------------------------------------------------------
    # Package is neither installed nor declared.
    #
    # We intentionally DO NOT install automatically.
    # The reasoned plan asks to declare it first.
    # ---------------------------------------------------------
    if status == "missing_and_undeclared":
        return [
            {
                "id": "declare_dependency",
                "title": f"Declare Python dependency: {package}",
                "reason": (
                    f"{package} is neither installed nor declared "
                    "by the project."
                ),
                "action": "declare_dependency",
                "package": package,
                "preview": (
                    f"Add {package} to the project's dependency "
                    "configuration before installation."
                ),
                "risk": "LOW",
            }
        ]

    # ---------------------------------------------------------
    # Python itself is unavailable.
    # ---------------------------------------------------------
    if status == "python_unavailable":
        return [
            {
                "id": "verify_environment",
                "title": "Verify Python environment",
                "reason": (
                    "FixPilot could not find a usable "
                    "Python interpreter."
                ),
                "action": "verify_environment",
                "package": package,
                "preview": (
                    "Verify the configured Python interpreter "
                    "and virtual environment."
                ),
                "risk": "LOW",
            }
        ]

    # Unknown state: fall back to the original planner.
    return build_error_repair_plan(
        category_code,
        error,
    )