from app.agent.error_fingerprint import fingerprint_error


def test_python_module_not_found():
    error = """
Traceback (most recent call last):
  File "test.py", line 1, in <module>
    import flask
ModuleNotFoundError: No module named 'flask'
"""

    result = fingerprint_error(error)

    assert result["language"] == "python"
    assert result["error_type"] == "ModuleNotFoundError"
    assert result["module"] == "flask"
    assert result["package"] == "flask"
    assert result["file"] == "test.py"
    assert result["line"] == 1
    assert result["confidence"] >= 0.9


def test_python_nested_module():
    error = """
Traceback (most recent call last):
  File "app.py", line 7, in <module>
    import requests.sessions
ModuleNotFoundError: No module named 'requests.sessions'
"""

    result = fingerprint_error(error)

    assert result["language"] == "python"
    assert result["error_type"] == "ModuleNotFoundError"
    assert result["module"] == "requests.sessions"
    assert result["package"] == "requests"


def test_python_import_error():
    error = """
Traceback (most recent call last):
  File "app.py", line 4, in <module>
    from flask import missing
ImportError: cannot import name 'missing' from 'flask'
"""

    result = fingerprint_error(error)

    assert result["language"] == "python"
    assert result["error_type"] == "ImportError"


def test_python_syntax_error():
    error = """
  File "app.py", line 10
    print("hello"
                ^
SyntaxError: '(' was never closed
"""

    result = fingerprint_error(error)

    assert result["language"] == "python"
    assert result["error_type"] == "SyntaxError"
    assert result["line"] == 10


def test_node_module_not_found():
    error = """
node:internal/modules/cjs/loader:1228
  throw err;
  ^

Error: Cannot find module 'express'
Require stack:
- C:\\project\\server.js
"""

    result = fingerprint_error(error)

    assert result["language"] == "node"
    assert result["error_type"] == "MODULE_NOT_FOUND"
    assert result["module"] == "express"
    assert result["package"] == "express"


def test_node_scoped_module():
    error = """
Error: Cannot find module '@nestjs/common'
Require stack:
- C:\\project\\main.js
"""

    result = fingerprint_error(error)

    assert result["language"] == "node"
    assert result["error_type"] == "MODULE_NOT_FOUND"
    assert result["module"] == "@nestjs/common"
    assert result["package"] == "@nestjs/common"


def test_node_port_conflict():
    error = """
Error: listen EADDRINUSE: address already in use :::3000
"""

    result = fingerprint_error(error)

    assert result["language"] == "node"
    assert result["error_type"] == "EADDRINUSE"


def test_unknown_error():
    result = fingerprint_error("Something completely unexpected happened.")

    assert result["error_type"] == "UnknownError"
    assert result["confidence"] == 0.0


def test_empty_error():
    result = fingerprint_error("")

    assert result["error_type"] == "UnknownError"
    assert result["confidence"] == 0.0


def test_explicit_language():
    error = """
Traceback (most recent call last):
  File "app.py", line 2, in <module>
    import flask
ModuleNotFoundError: No module named 'flask'
"""

    result = fingerprint_error(error, language="python")

    assert result["language"] == "python"
    assert result["error_type"] == "ModuleNotFoundError"