from app.context.dependencies import analyze_package
from app.context.environment import detect_environment
from app.context.interpreter import find_project_interpreter


def analyze_python_dependency(module_name, project_root="."):
    """
    Analyze a Python dependency using the target project's
    environment.

    FixPilot must distinguish between:

        FixPilot's Python environment
        and
        the target project's Python environment.

    A package installed globally does not mean it is installed
    in the target project's virtual environment.
    """

    project_interpreter = find_project_interpreter(
        project_root
    )

    environment = detect_environment(project_root)

    dependency = analyze_package(
        module_name,
        project_root,
        interpreter=project_interpreter,
    )

    installed = dependency["installed"]["installed"]
    version = dependency["installed"]["version"]
    declared = dependency["declared"]
    declaration = dependency["declaration"]

    if not installed:
        if declared:
            conclusion = (
                "Package is declared by the project "
                "but is not installed in the project environment."
            )
            recommended_action = "pip_install"
        else:
            conclusion = (
                "Package is not installed and is not "
                "declared by the project."
            )
            recommended_action = "ask_to_declare"
    else:
        if declared:
            conclusion = (
                "Package is installed and declared "
                "by the project."
            )
            recommended_action = "verify_environment"
        else:
            conclusion = (
                "Package is installed but not declared "
                "by the project."
            )
            recommended_action = "ask_to_declare"

    return {
        "module": module_name,
        "package": dependency["package"],
        "installed": installed,
        "installed_version": version,
        "declared": declared,
        "declaration": declaration,
        "python": environment["python"],
        "python_interpreter": project_interpreter,
        "virtual_environment": environment["virtual_environment"],
        "conclusion": conclusion,
        "recommended_action": recommended_action,
    }