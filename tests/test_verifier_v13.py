from app.repair.verifier import (
    verify_environment,
    verify_node_module,
    verify_plan,
    verify_python_import,
)


def test_verify_existing_python_module():
    result = verify_python_import("json")

    assert result["success"] is True
    assert result["module"] == "json"


def test_verify_missing_python_module():
    result = verify_python_import(
        "fixpilot_definitely_missing_module_xyz"
    )

    assert result["success"] is False


def test_verify_existing_node_module():
    result = verify_node_module("path")

    assert result["success"] is True
    assert result["package"] == "path"


def test_verify_missing_node_module(tmp_path):
    result = verify_node_module(
        "fixpilot_missing_node_module_xyz",
        cwd=tmp_path,
    )

    assert result["success"] is False


def test_verify_python_plan():
    plan = [
        {
            "action": "pip_install",
            "package": "json",
        }
    ]

    result = verify_plan(
        plan,
        [],
    )

    assert result["success"] is True


def test_verify_missing_python_plan():
    plan = [
        {
            "action": "pip_install",
            "package": "fixpilot_missing_module_xyz",
        }
    ]

    result = verify_plan(
        plan,
        [],
    )

    assert result["success"] is False


def test_verify_port_guidance_remains_unresolved():
    plan = [
        {
            "action": "inspect_port",
            "port": 3000,
        }
    ]

    result = verify_plan(
        plan,
        [],
    )

    assert result["success"] is False


def test_environment_verification_returns_result():
    result = verify_environment()

    assert "success" in result
    assert "checks" in result