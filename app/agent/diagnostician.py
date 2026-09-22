from app.rag import retrieve
from app.repair.planner import build_error_repair_plan


PATTERNS = [
    (
        "python_missing_module",
        ["modulenotfounderror", "no module named"],
        "Python dependency/environment",
        "A Python import failed because the referenced package is unavailable in the active environment.",
        "Inspect the active environment and install a declared dependency.",
    ),
    (
        "node_missing_module",
        ["cannot find module", "err_module_not_found"],
        "Node.js dependency",
        "Node cannot resolve a required package from the current project environment.",
        "Install the project's declared dependencies.",
    ),
    (
        "command_not_found",
        [
            "is not recognized as an internal or external command",
            "command not found",
        ],
        "PATH / tool installation",
        "The requested executable is unavailable through the current PATH.",
        "Inspect the tool installation and PATH.",
    ),
    (
        "port_in_use",
        ["eaddrinuse", "address already in use"],
        "Port conflict",
        "Another process is already listening on the requested local port.",
        "Identify the process or configure the application to use another port.",
    ),
]


def _classify(error):
    text = error.lower()

    for category, patterns, label, cause, recommendation in PATTERNS:
        if any(pattern in text for pattern in patterns):
            return category, label, cause, recommendation

    return (
        "unknown",
        "Unknown developer error",
        "The error does not match a supported FixPilot pattern yet.",
        "Collect more context and consult trusted documentation.",
    )


def diagnose_error(error):
    category_code, label, cause, recommendation = _classify(error)

    return {
        # Public human-readable category used by the UI and existing API.
        "category": label,

        # Internal machine-readable category used by repair logic.
        "category_code": category_code,

        "cause": cause,
        "confidence": "High" if category_code != "unknown" else "Low",
        "sources": retrieve(error, category_code),
        "recommendation": recommendation,

        # Planner receives the internal category code.
        "repair_plan": build_error_repair_plan(category_code, error),
    }