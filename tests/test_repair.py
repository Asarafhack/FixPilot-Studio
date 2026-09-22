from app.repair.planner import build_error_repair_plan
from app.repair.executor import execute_plan

def test_python_plan_is_allowlisted():
    plan = build_error_repair_plan(
        "python_missing_module",
        "ModuleNotFoundError: No module named 'definitely_missing_test_package'"
    )
    assert plan[0]["action"] == "pip_install"
    assert plan[0]["package"] == "definitely_missing_test_package"

def test_unsafe_python_package_is_blocked():
    plan = {"action": "pip_install", "package": "x; whoami"}
    result = execute_plan(plan)
    assert result["success"] is False
