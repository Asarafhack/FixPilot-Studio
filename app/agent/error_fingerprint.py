import re
from pathlib import Path
from typing import Any, Dict, Optional


class ErrorFingerprint:
    """
    Converts raw terminal/runtime errors into structured,
    machine-readable fingerprints for FixPilot's reasoning engine.
    """

    def __init__(
        self,
        language: str,
        error_type: str,
        message: str,
        confidence: float,
        file: Optional[str] = None,
        line: Optional[int] = None,
        column: Optional[int] = None,
        module: Optional[str] = None,
        package: Optional[str] = None,
        command: Optional[str] = None,
    ):
        self.language = language
        self.error_type = error_type
        self.message = message
        self.confidence = confidence
        self.file = file
        self.line = line
        self.column = column
        self.module = module
        self.package = package
        self.command = command

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "error_type": self.error_type,
            "message": self.message,
            "confidence": self.confidence,
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "module": self.module,
            "package": self.package,
            "command": self.command,
        }


def _extract_python_location(text: str):
    """
    Extract the most relevant Python traceback location.
    """
    matches = re.findall(
        r'File ["\'](.+?)["\'], line (\d+)',
        text,
    )

    if not matches:
        return None, None

    file_path, line_number = matches[-1]

    return file_path, int(line_number)


def _extract_python_command(text: str) -> Optional[str]:
    """
    Try to identify a Python command shown near the error.
    """
    patterns = [
        r'python(?:\.exe)?\s+([^\r\n]+)',
        r'py\s+([^\r\n]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return match.group(0).strip()

    return None


def _fingerprint_python(text: str) -> Optional[ErrorFingerprint]:
    """
    Identify common Python errors.
    """

    file_path, line_number = _extract_python_location(text)

    # ModuleNotFoundError
    match = re.search(
        r"ModuleNotFoundError:\s+No module named ['\"]?([^'\"\r\n]+)",
        text,
        re.IGNORECASE,
    )

    if match:
        module = match.group(1).strip()
        package = module.split(".")[0]

        return ErrorFingerprint(
            language="python",
            error_type="ModuleNotFoundError",
            message=match.group(0).strip(),
            confidence=0.99,
            file=file_path,
            line=line_number,
            module=module,
            package=package,
            command=_extract_python_command(text),
        )

    # ImportError
    match = re.search(
        r"ImportError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="python",
            error_type="ImportError",
            message=match.group(1).strip(),
            confidence=0.98,
            file=file_path,
            line=line_number,
            command=_extract_python_command(text),
        )

    # SyntaxError
    match = re.search(
        r"SyntaxError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="python",
            error_type="SyntaxError",
            message=match.group(1).strip(),
            confidence=0.99,
            file=file_path,
            line=line_number,
            command=_extract_python_command(text),
        )

    # NameError
    match = re.search(
        r"NameError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="python",
            error_type="NameError",
            message=match.group(1).strip(),
            confidence=0.98,
            file=file_path,
            line=line_number,
            command=_extract_python_command(text),
        )

    # TypeError
    match = re.search(
        r"TypeError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="python",
            error_type="TypeError",
            message=match.group(1).strip(),
            confidence=0.98,
            file=file_path,
            line=line_number,
            command=_extract_python_command(text),
        )

    # FileNotFoundError
    match = re.search(
        r"FileNotFoundError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="python",
            error_type="FileNotFoundError",
            message=match.group(1).strip(),
            confidence=0.99,
            file=file_path,
            line=line_number,
            command=_extract_python_command(text),
        )

    return None


def _extract_node_location(text: str):
    """
    Extract Node.js file and line information.
    """
    match = re.search(
        r"(?:at\s+)?(?:file://)?(.+?):(\d+):(\d+)",
        text,
        re.IGNORECASE,
    )

    if not match:
        return None, None, None

    file_path = match.group(1)
    line = int(match.group(2))
    column = int(match.group(3))

    return file_path, line, column


def _fingerprint_node(text: str) -> Optional[ErrorFingerprint]:
    """
    Identify common Node.js errors.
    """

    file_path, line_number, column = _extract_node_location(text)

    # MODULE_NOT_FOUND
    match = re.search(
        r"(?:Error:\s*)?Cannot find module ['\"]([^'\"]+)['\"]",
        text,
        re.IGNORECASE,
    )

    if match:
        module = match.group(1).strip()

        package = module

        if module.startswith("@"):
            parts = module.split("/")

            if len(parts) >= 2:
                package = "/".join(parts[:2])

        elif "/" in module:
            package = module.split("/")[0]

        return ErrorFingerprint(
            language="node",
            error_type="MODULE_NOT_FOUND",
            message=match.group(0).strip(),
            confidence=0.99,
            file=file_path,
            line=line_number,
            column=column,
            module=module,
            package=package,
        )

    # EADDRINUSE
    match = re.search(
        r"EADDRINUSE.*?(?:port\s+)?(\d+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="node",
            error_type="EADDRINUSE",
            message=match.group(0).strip(),
            confidence=0.99,
            file=file_path,
            line=line_number,
            column=column,
        )

    # SyntaxError
    match = re.search(
        r"SyntaxError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="node",
            error_type="SyntaxError",
            message=match.group(1).strip(),
            confidence=0.98,
            file=file_path,
            line=line_number,
            column=column,
        )

    # ReferenceError
    match = re.search(
        r"ReferenceError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="node",
            error_type="ReferenceError",
            message=match.group(1).strip(),
            confidence=0.98,
            file=file_path,
            line=line_number,
            column=column,
        )

    # TypeError
    match = re.search(
        r"TypeError:\s*(.+)",
        text,
        re.IGNORECASE,
    )

    if match:
        return ErrorFingerprint(
            language="node",
            error_type="TypeError",
            message=match.group(1).strip(),
            confidence=0.98,
            file=file_path,
            line=line_number,
            column=column,
        )

    return None


def fingerprint_error(
    error_text: str,
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analyze raw error text and return a structured fingerprint.

    If language is supplied, the corresponding parser is preferred.
    Otherwise FixPilot attempts Python and Node.js detection.
    """

    if not isinstance(error_text, str):
        raise TypeError("error_text must be a string")

    text = error_text.strip()

    if not text:
        return {
            "language": "unknown",
            "error_type": "UnknownError",
            "message": "",
            "confidence": 0.0,
            "file": None,
            "line": None,
            "column": None,
            "module": None,
            "package": None,
            "command": None,
        }

    normalized_language = language.lower().strip() if language else None

    fingerprint = None

    if normalized_language in {"python", "py"}:
        fingerprint = _fingerprint_python(text)

    elif normalized_language in {"node", "nodejs", "javascript", "js"}:
        fingerprint = _fingerprint_node(text)

    else:
        # Try Python first.
        fingerprint = _fingerprint_python(text)

        # Then Node.js.
        if fingerprint is None:
            fingerprint = _fingerprint_node(text)

    if fingerprint is not None:
        return fingerprint.to_dict()

    return {
        "language": normalized_language or "unknown",
        "error_type": "UnknownError",
        "message": text[:2000],
        "confidence": 0.0,
        "file": None,
        "line": None,
        "column": None,
        "module": None,
        "package": None,
        "command": None,
    }