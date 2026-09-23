from app.agent.project_reasoner import reason_about_project


def test_project_reasoner_contains_root_cause(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "requests==2.31.0\n",
        encoding="utf-8",
    )

    result = reason_about_project(
        """
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import flask
ModuleNotFoundError: No module named 'flask'
""",
        str(tmp_path),
    )

    assert "diagnosis" in result
    assert "dependency_analysis" in result
    assert "root_cause" in result

    root_cause = result["root_cause"]

    assert "cause_code" in root_cause
    assert "root_cause" in root_cause
    assert "confidence" in root_cause
    assert "evidence" in root_cause
    assert "recommended_action" in root_cause


def test_project_reasoner_uses_fingerprint(tmp_path):
    result = reason_about_project(
        """
Traceback (most recent call last):
  File "server.py", line 5, in <module>
    import flask
ModuleNotFoundError: No module named 'flask'
""",
        str(tmp_path),
    )

    fingerprint = result["diagnosis"]["fingerprint"]

    assert fingerprint["language"] == "python"
    assert fingerprint["error_type"] == "ModuleNotFoundError"
    assert fingerprint["module"] == "flask"

    root_cause = result["root_cause"]

    assert root_cause["package"] == "flask"


def test_project_reasoner_preserves_dependency_analysis(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        "flask==3.0.3\n",
        encoding="utf-8",
    )

    result = reason_about_project(
        """
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import flask
ModuleNotFoundError: No module named 'flask'
""",
        str(tmp_path),
    )

    dependency = result["dependency_analysis"]

    assert dependency is not None
    assert dependency["declared"] is True

    root_cause = result["root_cause"]

    assert root_cause["cause_code"] in {
        "dependency_not_installed",
        "environment_mismatch",
    }