from app.agent import diagnose_error

def test_python_diagnosis():
    result = diagnose_error("ModuleNotFoundError: No module named flask")
    assert result["category"] == "Python dependency/environment"
    assert result["repair_plan"][0]["action"] == "pip_install"

def test_node_diagnosis():
    result = diagnose_error("Error: Cannot find module 'express'")
    assert result["category"] == "Node.js dependency"
    assert result["repair_plan"][0]["action"] == "npm_install"
