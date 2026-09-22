from app.agent.diagnostician import diagnose_error
from app.agent.dependency_reasoner import analyze_python_dependency
from app.context.scanner import scan_project, project_summary
from app.rag import retrieve


def _extract_python_module(error):
    import re

    match = re.search(
        r"No module named\s+['\"]?([A-Za-z0-9_.-]+)['\"]?",
        error,
        re.I,
    )

    if not match:
        return None

    return match.group(1).split(".")[0]


def reason_about_project(error, project_root="."):
    context = scan_project(project_root)
    diagnosis = diagnose_error(error)

    evidence = retrieve(
        error + "\n" + project_summary(context),
        limit=5,
    )

    hints = []
    dependency_analysis = None

    manifests = context["manifests"]

    if diagnosis["category"] == "Python dependency/environment":
        module = _extract_python_module(error)

        if module:
            dependency_analysis = analyze_python_dependency(
                module,
                project_root,
            )

            if dependency_analysis["installed"]:
                if dependency_analysis["declared"]:
                    hints.append(
                        "The package is installed and declared by the project."
                    )
                else:
                    hints.append(
                        "The package is installed but not declared by the project."
                    )

            else:
                if dependency_analysis["declared"]:
                    hints.append(
                        "The package is declared by the project but is not installed."
                    )
                else:
                    hints.append(
                        "The package is neither installed nor declared by the project."
                    )

    if (
        "requirements.txt" in manifests
        and diagnosis["category"] == "Python dependency/environment"
    ):
        hints.append(
            "requirements.txt exists; verify the missing package is declared before installing it."
        )

    if (
        "pyproject.toml" in manifests
        and diagnosis["category"] == "Python dependency/environment"
    ):
        hints.append(
            "pyproject.toml exists; the project may use managed dependency configuration."
        )

    if (
        "package.json" in manifests
        and diagnosis["category"] == "Node.js dependency"
    ):
        hints.append(
            "package.json exists; inspect declared dependencies before changing the environment."
        )

    return {
        "diagnosis": diagnosis,
        "context": context,
        "project_summary": project_summary(context),
        "evidence": evidence,
        "project_hints": hints,
        "dependency_analysis": dependency_analysis,
    }