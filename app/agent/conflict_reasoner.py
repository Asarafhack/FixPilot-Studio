from app.context.dependencies import (
    import_to_package,
    analyze_package,
)
from app.context.environment import detect_environment
from app.context.interpreter import find_project_interpreter


def analyze_dependency_conflict(
    module_name,
    project_root=".",
):
    """
    Analyze whether a Python dependency problem is caused by:

    - missing package
    - undeclared package
    - missing installation
    - environment mismatch
    - version information

    Dependency installation state is checked against the
    target project's Python interpreter, not FixPilot's
    own Python environment.
    """

    package = import_to_package(module_name)

    environment = detect_environment(
        project_root
    )

    project_interpreter = find_project_interpreter(
        project_root
    )

    dependency = analyze_package(
        module_name,
        project_root,
        interpreter=project_interpreter,
    )

    installed_info = dependency.get(
        "installed"
    )

    if isinstance(installed_info, dict):
        installed = installed_info.get(
            "installed",
            False,
        )

        installed_version = installed_info.get(
            "version"
        )
    else:
        installed = bool(installed_info)
        installed_version = None

    declared = dependency.get(
        "declared",
        False,
    )

    result = {
        "module": module_name,
        "package": package,
        "installed": installed,
        "installed_version": installed_version,
        "declared": declared,
        "declaration": dependency.get(
            "declaration"
        ),
        "environment": environment,
        "interpreter": project_interpreter,
        "status": None,
        "recommended_action": None,
    }

    # ---------------------------------------------------------
    # PYTHON UNAVAILABLE
    # ---------------------------------------------------------

    if not environment["python"]["available"]:
        result["status"] = "python_unavailable"
        result["recommended_action"] = (
            "verify_environment"
        )

        return result

    # ---------------------------------------------------------
    # INTERPRETER UNAVAILABLE
    # ---------------------------------------------------------

    if not project_interpreter:
        result["status"] = (
            "project_interpreter_unavailable"
        )
        result["recommended_action"] = (
            "verify_environment"
        )

        return result

    # ---------------------------------------------------------
    # INSTALLED + DECLARED
    # ---------------------------------------------------------

    if installed and declared:
        result["status"] = "healthy"
        result["recommended_action"] = (
            "verify_import"
        )

        return result

    # ---------------------------------------------------------
    # INSTALLED + NOT DECLARED
    # ---------------------------------------------------------

    if installed and not declared:
        result["status"] = (
            "installed_not_declared"
        )
        result["recommended_action"] = (
            "ask_to_declare"
        )

        return result

    # ---------------------------------------------------------
    # NOT INSTALLED + DECLARED
    # ---------------------------------------------------------

    if not installed and declared:
        result["status"] = (
            "declared_not_installed"
        )
        result["recommended_action"] = (
            "pip_install"
        )

        return result

    # ---------------------------------------------------------
    # NOT INSTALLED + NOT DECLARED
    # ---------------------------------------------------------

    result["status"] = (
        "missing_and_undeclared"
    )

    result["recommended_action"] = (
        "ask_to_declare"
    )

    return result