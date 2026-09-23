from app.agent.diagnostician import diagnose_error


def test_diagnosis_contains_python_fingerprint():
    error = """
Traceback (most recent call last):
  File "app.py", line 4, in <module>
    import flask
ModuleNotFoundError: No module named 'flask'
"""

    result = diagnose_error(error)

    assert result["category_code"] == "python_missing_module"

    fingerprint = result["fingerprint"]

    assert fingerprint["language"] == "python"
    assert fingerprint["error_type"] == "ModuleNotFoundError"
    assert fingerprint["module"] == "flask"
    assert fingerprint["package"] == "flask"
    assert fingerprint["file"] == "app.py"
    assert fingerprint["line"] == 4


def test_diagnosis_contains_node_fingerprint():
    error = """
Error: Cannot find module 'express'
Require stack:
- C:\\project\\server.js
"""

    result = diagnose_error(error)

    assert result["category_code"] == "node_missing_module"

    fingerprint = result["fingerprint"]

    assert fingerprint["language"] == "node"
    assert fingerprint["error_type"] == "MODULE_NOT_FOUND"
    assert fingerprint["module"] == "express"
    assert fingerprint["package"] == "express"


def test_existing_diagnosis_fields_are_preserved():
    error = """
Traceback (most recent call last):
  File "test.py", line 1, in <module>
    import flask
ModuleNotFoundError: No module named 'flask'
"""

    result = diagnose_error(error)

    assert "category" in result
    assert "category_code" in result
    assert "cause" in result
    assert "confidence" in result
    assert "sources" in result
    assert "recommendation" in result
    assert "repair_plan" in result
    assert "fingerprint" in result