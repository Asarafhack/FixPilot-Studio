from app.repair.validator import (
    is_repair_plan_safe,
    validate_repair_plan,
)


def test_allows_safe_pip_install(tmp_path):
    plan = {
        "action": "pip_install",
        "package": "flask",
        "risk": "LOW",
    }

    result = validate_repair_plan(plan, tmp_path)

    assert result["allowed"] is True
    assert result["action"] == "pip_install"


def test_allows_safe_npm_install(tmp_path):
    plan = {
        "action": "npm_install",
        "package": "express",
        "risk": "LOW",
    }

    assert is_repair_plan_safe(plan, tmp_path)


def test_allows_scoped_npm_package(tmp_path):
    plan = {
        "action": "npm_install",
        "package": "@types/node",
        "risk": "LOW",
    }

    assert is_repair_plan_safe(plan, tmp_path)


def test_blocks_unknown_action(tmp_path):
    plan = {
        "action": "run_command",
        "command": "whoami",
        "risk": "HIGH",
    }

    result = validate_repair_plan(plan, tmp_path)

    assert result["allowed"] is False


def test_blocks_shell_injection_package(tmp_path):
    plan = {
        "action": "pip_install",
        "package": "flask && whoami",
        "risk": "LOW",
    }

    result = validate_repair_plan(plan, tmp_path)

    assert result["allowed"] is False


def test_blocks_pipe_injection(tmp_path):
    plan = {
        "action": "pip_install",
        "package": "flask | powershell",
        "risk": "LOW",
    }

    result = validate_repair_plan(plan, tmp_path)

    assert result["allowed"] is False


def test_blocks_command_field(tmp_path):
    plan = {
        "action": "pip_install",
        "package": "flask",
        "command": "pip install flask && whoami",
        "risk": "LOW",
    }

    result = validate_repair_plan(plan, tmp_path)

    assert result["allowed"] is False


def test_allows_valid_port(tmp_path):
    plan = {
        "action": "inspect_port",
        "port": 3000,
        "risk": "LOW",
    }

    assert is_repair_plan_safe(plan, tmp_path)


def test_blocks_invalid_port(tmp_path):
    plan = {
        "action": "inspect_port",
        "port": 70000,
        "risk": "LOW",
    }

    result = validate_repair_plan(plan, tmp_path)

    assert result["allowed"] is False


def test_blocks_missing_project_root(tmp_path):
    project = tmp_path / "does-not-exist"

    plan = {
        "action": "pip_install",
        "package": "flask",
        "risk": "LOW",
    }

    result = validate_repair_plan(plan, project)

    assert result["allowed"] is False


def test_allows_verify_import(tmp_path):
    plan = {
        "action": "verify_import",
        "package": "flask",
        "risk": "LOW",
    }

    assert is_repair_plan_safe(plan, tmp_path)