from app.repair.executor import execute_plan


def test_executor_allows_safe_pip_install(tmp_path):
    plan = {
        "action": "pip_install",
        "package": "flask",
        "risk": "LOW",
    }

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["blocked"] is False
    assert result["action"] == "pip_install"


def test_executor_blocks_shell_injection(tmp_path):
    plan = {
        "action": "pip_install",
        "package": "flask && whoami",
        "risk": "LOW",
    }

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is False
    assert result["blocked"] is True
    assert "safety validator" in result["message"].lower()


def test_executor_blocks_arbitrary_command(tmp_path):
    plan = {
        "action": "run_command",
        "command": "whoami",
        "risk": "HIGH",
    }

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is False
    assert result["blocked"] is True


def test_executor_allows_port_inspection(tmp_path):
    plan = {
        "action": "inspect_port",
        "port": 3000,
        "risk": "LOW",
    }

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is True
    assert result["blocked"] is False
    assert result["port"] == 3000


def test_executor_allows_environment_verification(tmp_path):
    plan = {
        "action": "verify_environment",
        "risk": "LOW",
    }

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is True
    assert result["blocked"] is False


def test_executor_allows_dependency_declaration(tmp_path):
    plan = {
        "action": "declare_dependency",
        "package": "flask",
        "risk": "LOW",
    }

    result = execute_plan(
        plan,
        cwd=tmp_path,
    )

    assert result["success"] is True
    assert result["blocked"] is False