from app.agent.root_cause import analyze_root_cause


def python_fingerprint():
    return {
        "language": "python",
        "error_type": "ModuleNotFoundError",
        "module": "flask",
        "package": "flask",
        "message": "No module named 'flask'",
        "confidence": 0.99,
    }


def node_fingerprint():
    return {
        "language": "node",
        "error_type": "MODULE_NOT_FOUND",
        "module": "express",
        "package": "express",
        "message": "Cannot find module 'express'",
        "confidence": 0.99,
    }


def test_installed_but_not_declared():
    result = analyze_root_cause(
        python_fingerprint(),
        dependency={
            "installed": True,
            "declared": False,
        },
    )

    assert result["cause_code"] == "dependency_not_declared"
    assert result["dependency_state"] == "installed_not_declared"
    assert result["confidence"] >= 0.9
    assert "flask" in result["root_cause"]


def test_declared_but_not_installed():
    result = analyze_root_cause(
        python_fingerprint(),
        dependency={
            "installed": False,
            "declared": True,
        },
    )

    assert result["cause_code"] == "dependency_not_installed"
    assert result["dependency_state"] == "declared_not_installed"


def test_missing_and_undeclared():
    result = analyze_root_cause(
        python_fingerprint(),
        dependency={
            "installed": False,
            "declared": False,
        },
    )

    assert result["cause_code"] == "missing_dependency"
    assert result["dependency_state"] == "missing_and_undeclared"


def test_installed_and_declared_environment_mismatch():
    result = analyze_root_cause(
        python_fingerprint(),
        dependency={
            "installed": True,
            "declared": True,
        },
    )

    assert result["cause_code"] == "environment_mismatch"
    assert result["dependency_state"] == "healthy"


def test_node_missing_dependency():
    result = analyze_root_cause(
        node_fingerprint(),
        dependency={
            "installed": False,
            "declared": False,
        },
    )

    assert result["cause_code"] == "node_missing_dependency"
    assert result["dependency_state"] == "missing_and_undeclared"


def test_node_declared_not_installed():
    result = analyze_root_cause(
        node_fingerprint(),
        dependency={
            "installed": False,
            "declared": True,
        },
    )

    assert result["cause_code"] == "node_dependency_not_installed"


def test_port_conflict():
    result = analyze_root_cause(
        {
            "language": "node",
            "error_type": "EADDRINUSE",
            "message": "listen EADDRINUSE: address already in use :::3000",
            "confidence": 0.99,
        }
    )

    assert result["cause_code"] == "port_conflict"
    assert result["confidence"] >= 0.9


def test_unknown_error():
    result = analyze_root_cause(
        {
            "language": "unknown",
            "error_type": "UnknownError",
            "message": "Something unexpected happened.",
            "confidence": 0.0,
        }
    )

    assert result["cause_code"] == "unknown"
    assert result["dependency_state"] == "unknown"
    assert result["confidence"] < 0.5


def test_result_contains_reasoning_fields():
    result = analyze_root_cause(
        python_fingerprint(),
        dependency={
            "installed": True,
            "declared": False,
        },
        environment={
            "python": {
                "version": "3.11.0",
            }
        },
    )

    assert "cause_code" in result
    assert "root_cause" in result
    assert "confidence" in result
    assert "evidence" in result
    assert "recommended_action" in result
    assert "language" in result
    assert "error_type" in result
    assert "dependency_state" in result