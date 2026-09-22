from app.repair.planner import build_reasoned_repair_plan


def test_installed_undeclared_uses_declaration_plan(tmp_path):
    result = build_reasoned_repair_plan(
        "ModuleNotFoundError: No module named flask",
        tmp_path,
    )

    assert len(result) == 1
    assert result[0]["action"] == "declare_dependency"
    assert result[0]["package"] == "flask"


def test_declared_installed_uses_verify_plan(tmp_path):
    requirements = tmp_path / "requirements.txt"

    requirements.write_text(
        "Flask>=3.0\n",
        encoding="utf-8",
    )

    result = build_reasoned_repair_plan(
        "ModuleNotFoundError: No module named flask",
        tmp_path,
    )

    assert len(result) == 1
    assert result[0]["action"] == "verify_import"


def test_declared_missing_uses_install_plan(tmp_path):
    requirements = tmp_path / "requirements.txt"

    requirements.write_text(
        "some-package>=1.0\n",
        encoding="utf-8",
    )

    result = build_reasoned_repair_plan(
        "ModuleNotFoundError: No module named some_package",
        tmp_path,
    )

    assert len(result) == 1
    assert result[0]["action"] == "pip_install"