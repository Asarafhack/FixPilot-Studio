from typing import Any, Dict, List, Optional


def _confidence(value: float) -> float:
    """Keep confidence safely between 0 and 1."""
    return max(0.0, min(1.0, round(value, 2)))


def _dependency_state(dependency: Optional[Dict[str, Any]]) -> str:
    """
    Normalize dependency information from FixPilot's dependency reasoner.
    """

    if not dependency:
        return "unknown"

    installed = dependency.get("installed")

    if isinstance(installed, dict):
        installed = installed.get("installed", False)

    declared = dependency.get("declared", False)

    if installed and declared:
        return "healthy"

    if installed and not declared:
        return "installed_not_declared"

    if not installed and declared:
        return "declared_not_installed"

    if not installed and not declared:
        return "missing_and_undeclared"

    return "unknown"


def analyze_root_cause(
    fingerprint: Dict[str, Any],
    dependency: Optional[Dict[str, Any]] = None,
    environment: Optional[Dict[str, Any]] = None,
    conflict: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Determine the most likely root cause from FixPilot evidence.

    This engine does not execute repairs.
    It only produces structured reasoning that can later be
    consumed by the repair planner and safety layer.
    """

    language = fingerprint.get("language", "unknown")
    error_type = fingerprint.get("error_type", "UnknownError")
    module = fingerprint.get("module")
    package = fingerprint.get("package") or module

    evidence: List[str] = []
    cause_code = "unknown"
    root_cause = "Unable to determine a specific root cause."
    recommended_action = "Collect additional project and environment context."
    confidence = 0.35

    dependency_state = _dependency_state(dependency)

    # ---------------------------------------------------------
    # Python dependency analysis
    # ---------------------------------------------------------

    if language == "python" and error_type == "ModuleNotFoundError":
        if dependency_state == "installed_not_declared":
            cause_code = "dependency_not_declared"
            root_cause = (
                f"Python package '{package}' is installed in the current "
                "environment but is not declared by the project."
            )
            recommended_action = (
                f"Declare '{package}' in the project's dependency manifest "
                "and verify the project environment."
            )

            evidence.extend(
                [
                    "Python ModuleNotFoundError detected.",
                    f"Required package identified as '{package}'.",
                    "Package is installed.",
                    "Package is not declared by the project.",
                ]
            )

            confidence = 0.97

        elif dependency_state == "declared_not_installed":
            cause_code = "dependency_not_installed"
            root_cause = (
                f"Python package '{package}' is declared by the project "
                "but is not installed in the active environment."
            )
            recommended_action = (
                f"Install the project's declared dependency '{package}' "
                "using the active project environment."
            )

            evidence.extend(
                [
                    "Python ModuleNotFoundError detected.",
                    f"Required package identified as '{package}'.",
                    "Package is declared by the project.",
                    "Package is not installed.",
                ]
            )

            confidence = 0.98

        elif dependency_state == "missing_and_undeclared":
            cause_code = "missing_dependency"
            root_cause = (
                f"Python package '{package}' is missing and is not declared "
                "by the project."
            )
            recommended_action = (
                f"Verify that '{package}' is actually required, then declare "
                "and install it in the project environment."
            )

            evidence.extend(
                [
                    "Python ModuleNotFoundError detected.",
                    f"Required package identified as '{package}'.",
                    "Package is not installed.",
                    "Package is not declared by the project.",
                ]
            )

            confidence = 0.94

        elif dependency_state == "healthy":
            cause_code = "environment_mismatch"
            root_cause = (
                f"Package '{package}' appears installed and declared, "
                "but the running interpreter cannot import it."
            )
            recommended_action = (
                "Verify the interpreter, virtual environment, and project "
                "runtime used to execute the application."
            )

            evidence.extend(
                [
                    "Python ModuleNotFoundError detected.",
                    f"Required package identified as '{package}'.",
                    "Package appears installed.",
                    "Package appears declared by the project.",
                    "Runtime environment may differ from the inspected environment.",
                ]
            )

            confidence = 0.91

        else:
            cause_code = "python_dependency_unknown"
            root_cause = (
                f"Python cannot import '{package}', but dependency state "
                "could not be established."
            )
            recommended_action = (
                "Inspect the active Python interpreter, virtual environment, "
                "and project dependency files."
            )

            evidence.extend(
                [
                    "Python ModuleNotFoundError detected.",
                    f"Required package identified as '{package}'.",
                    "Dependency state is incomplete.",
                ]
            )

            confidence = 0.78

    # ---------------------------------------------------------
    # Node.js dependency analysis
    # ---------------------------------------------------------

    elif language == "node" and error_type == "MODULE_NOT_FOUND":
        if dependency_state == "installed_not_declared":
            cause_code = "node_dependency_not_declared"
            root_cause = (
                f"Node package '{package}' is available in the environment "
                "but is not declared by the project."
            )
            recommended_action = (
                f"Declare '{package}' in package.json and verify the "
                "project's dependency installation."
            )

            evidence.extend(
                [
                    "Node MODULE_NOT_FOUND detected.",
                    f"Required package identified as '{package}'.",
                    "Package appears installed.",
                    "Package is not declared by the project.",
                ]
            )

            confidence = 0.95

        elif dependency_state == "declared_not_installed":
            cause_code = "node_dependency_not_installed"
            root_cause = (
                f"Node package '{package}' is declared in package.json "
                "but is not installed in the current project."
            )
            recommended_action = (
                "Install the project's declared Node dependencies and "
                "verify node_modules."
            )

            evidence.extend(
                [
                    "Node MODULE_NOT_FOUND detected.",
                    f"Required package identified as '{package}'.",
                    "Package is declared by the project.",
                    "Package is not installed.",
                ]
            )

            confidence = 0.98

        elif dependency_state == "missing_and_undeclared":
            cause_code = "node_missing_dependency"
            root_cause = (
                f"Node package '{package}' cannot be resolved and is not "
                "declared by the project."
            )
            recommended_action = (
                f"Verify whether '{package}' is required, then declare and "
                "install it using the project's package manager."
            )

            evidence.extend(
                [
                    "Node MODULE_NOT_FOUND detected.",
                    f"Required package identified as '{package}'.",
                    "Package is not installed.",
                    "Package is not declared by the project.",
                ]
            )

            confidence = 0.94

        else:
            cause_code = "node_environment_mismatch"
            root_cause = (
                f"Node cannot resolve '{package}', but the available "
                "dependency evidence is incomplete."
            )
            recommended_action = (
                "Inspect package.json, lockfiles, node_modules, and the "
                "active Node/package-manager environment."
            )

            evidence.extend(
                [
                    "Node MODULE_NOT_FOUND detected.",
                    f"Required package identified as '{package}'.",
                    "Dependency state is incomplete.",
                ]
            )

            confidence = 0.78

    # ---------------------------------------------------------
    # Port conflicts
    # ---------------------------------------------------------

    elif error_type == "EADDRINUSE" or "port" in str(
        fingerprint.get("message", "")
    ).lower():
        cause_code = "port_conflict"
        root_cause = (
            "Another process is already using the requested local port."
        )
        recommended_action = (
            "Identify the process using the port and either stop it "
            "or configure the application to use another port."
        )

        evidence.extend(
            [
                "Port conflict error detected.",
                "The requested local network address is already in use.",
            ]
        )

        confidence = 0.99

    # ---------------------------------------------------------
    # Command / PATH problems
    # ---------------------------------------------------------

    elif error_type in {
        "CommandNotFound",
        "COMMAND_NOT_FOUND",
    }:
        cause_code = "missing_command_or_path"
        root_cause = (
            "The requested executable is unavailable through the current "
            "environment PATH."
        )
        recommended_action = (
            "Verify that the required tool is installed and that its "
            "installation directory is available through PATH."
        )

        evidence.extend(
            [
                "Command-not-found condition detected.",
                "Executable resolution failed.",
            ]
        )

        confidence = 0.95

    # ---------------------------------------------------------
    # Generic fallback
    # ---------------------------------------------------------

    else:
        evidence.append(
            f"Fingerprint identified language='{language}' "
            f"and error_type='{error_type}'."
        )

        if module:
            evidence.append(f"Referenced module: '{module}'.")

        if package:
            evidence.append(f"Referenced package: '{package}'.")

        if environment:
            evidence.append("Environment context was supplied.")

        if conflict:
            evidence.append("Conflict analysis was supplied.")

    return {
        "cause_code": cause_code,
        "root_cause": root_cause,
        "confidence": _confidence(confidence),
        "evidence": evidence,
        "recommended_action": recommended_action,
        "language": language,
        "error_type": error_type,
        "module": module,
        "package": package,
        "dependency_state": dependency_state,
    }