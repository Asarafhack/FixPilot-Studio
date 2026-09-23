from app.agent.diagnostician import diagnose_error
from app.agent.dependency_reasoner import analyze_python_dependency
from app.agent.root_cause import analyze_root_cause
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


def _normalize_dependency_analysis(analysis):
    """
    Convert FixPilot's dependency-reasoner result into the
    normalized structure expected by the root-cause engine.
    """

    if not analysis:
        return None

    installed = analysis.get("installed", False)

    if isinstance(installed, dict):
        installed = installed.get("installed", False)

    return {
        "installed": bool(installed),
        "declared": bool(analysis.get("declared", False)),
        "package": analysis.get("package"),
        "module": analysis.get("module"),
        "installed_version": analysis.get("installed_version"),
        "declaration": analysis.get("declaration"),
        "recommended_action": analysis.get("recommended_action"),
    }


def reason_about_project(error, project_root="."):
    """
    Build a complete project-aware diagnosis.

    Flow:

        Error
          ↓
        Diagnosis
          ↓
        Fingerprint
          ↓
        Project Context
          ↓
        Dependency Analysis
          ↓
        Root Cause
          ↓
        Evidence / Recommendation
    """

    context = scan_project(project_root)
    diagnosis = diagnose_error(error)

    evidence = retrieve(
        error + "\n" + project_summary(context),
        limit=5,
    )

    hints = []
    dependency_analysis = None

    manifests = context["manifests"]

    # ---------------------------------------------------------
    # Python dependency analysis
    # ---------------------------------------------------------

    if diagnosis["category"] == "Python dependency/environment":
        module = _extract_python_module(error)

        # Prefer the structured fingerprint when available.
        fingerprint = diagnosis.get("fingerprint", {})

        fingerprint_module = fingerprint.get("module")

        if fingerprint_module:
            module = fingerprint_module.split(".")[0]

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

    # ---------------------------------------------------------
    # Manifest-specific hints
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # Root cause analysis
    # ---------------------------------------------------------

    normalized_dependency = _normalize_dependency_analysis(
        dependency_analysis
    )

    root_cause = analyze_root_cause(
        fingerprint=diagnosis.get(
            "fingerprint",
            {
                "language": "unknown",
                "error_type": "UnknownError",
                "message": error,
                "confidence": 0.0,
            },
        ),
        dependency=normalized_dependency,
        environment=context.get("environment"),
    )

    # ---------------------------------------------------------
    # Return complete project reasoning
    # ---------------------------------------------------------

    return {
        "diagnosis": diagnosis,
        "context": context,
        "project_summary": project_summary(context),
        "evidence": evidence,
        "project_hints": hints,

        # Existing V1.1 dependency analysis remains available.
        "dependency_analysis": dependency_analysis,

        # New V1.2 structured root-cause analysis.
        "root_cause": root_cause,
    }