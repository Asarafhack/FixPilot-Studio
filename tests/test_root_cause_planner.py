from app.repair.planner import build_reasoned_repair_plan


MISSING_PACKAGE = "fixpilot_test_missing_package_xyz"


def test_planner_uses_dependency_not_declared(tmp_path):
    result = build_reasoned_repair_plan(
        f"""
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import {MISSING_PACKAGE}
ModuleNotFoundError: No module named '{MISSING_PACKAGE}'
""",
        str(tmp_path),
    )

    assert len(result) == 1

    plan = result[0]

    assert plan["action"] == "declare_dependency"
    assert plan["package"] == MISSING_PACKAGE
    assert plan["cause_code"] == "missing_dependency"


def test_planner_uses_declared_not_installed(tmp_path):
    requirements = tmp_path / "requirements.txt"
    requirements.write_text(
        f"{MISSING_PACKAGE}==1.0.0\n",
        encoding="utf-8",
    )

    result = build_reasoned_repair_plan(
        f"""
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import {MISSING_PACKAGE}
ModuleNotFoundError: No module named '{MISSING_PACKAGE}'
""",
        str(tmp_path),
    )

    assert len(result) == 1

    plan = result[0]

    assert plan["action"] == "pip_install"
    assert plan["package"] == MISSING_PACKAGE
    assert plan["cause_code"] == "dependency_not_installed"


def test_planner_uses_missing_dependency_state(tmp_path):
    result = build_reasoned_repair_plan(
        f"""
Traceback (most recent call last):
  File "app.py", line 1, in <module>
    import {MISSING_PACKAGE}
ModuleNotFoundError: No module named '{MISSING_PACKAGE}'
""",
        str(tmp_path),
    )

    assert len(result) == 1

    plan = result[0]

    assert plan["action"] == "declare_dependency"
    assert plan["package"] == MISSING_PACKAGE
    assert plan["cause_code"] == "missing_dependency"


def test_planner_preserves_node_behavior(tmp_path):
    result = build_reasoned_repair_plan(
        """
Error: Cannot find module 'express'
Require stack:
- C:\\project\\server.js
""",
        str(tmp_path),
    )

    assert len(result) == 1

    plan = result[0]

    assert plan["action"] == "npm_install"
    assert plan["package"] == "express"


def test_planner_preserves_port_behavior(tmp_path):
    result = build_reasoned_repair_plan(
        "Error: listen EADDRINUSE: address already in use :::3000",
        str(tmp_path),
    )

    assert len(result) == 1

    plan = result[0]

    assert plan["action"] == "inspect_port"
    assert plan["port"] == 3000