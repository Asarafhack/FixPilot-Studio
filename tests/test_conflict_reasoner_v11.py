from app.agent.conflict_reasoner import analyze_dependency_conflict


def test_installed_but_undeclared_package(tmp_path):
    result = analyze_dependency_conflict(
        "flask",
        tmp_path,
    )

    assert result["package"] == "flask"
    assert result["installed"] is True
    assert result["declared"] is False
    assert result["status"] == "installed_not_declared"
    assert result["recommended_action"] == "ask_to_declare"


def test_declared_package(tmp_path):
    requirements = tmp_path / "requirements.txt"

    requirements.write_text(
        "Flask>=3.0\n",
        encoding="utf-8",
    )

    result = analyze_dependency_conflict(
        "flask",
        tmp_path,
    )

    assert result["declared"] is True
    assert result["status"] == "healthy"
    assert result["recommended_action"] == "verify_import"