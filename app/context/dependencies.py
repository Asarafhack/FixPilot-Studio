import json
import re
import subprocess
from importlib import metadata
from pathlib import Path


IMPORT_PACKAGE_MAP = {
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "sklearn": "scikit-learn",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "jwt": "PyJWT",
    "Crypto": "pycryptodome",
    "dateutil": "python-dateutil",
}


def normalize_package_name(name):
    if not name:
        return ""

    return (
        name.strip()
        .lower()
        .replace("-", "_")
        .replace(".", "_")
    )


def import_to_package(module_name):
    if not module_name:
        return None

    root = module_name.strip().split(".")[0]

    return IMPORT_PACKAGE_MAP.get(root, root)


def installed_package(package_name, interpreter=None):
    """
    Determine whether a package is installed.

    When an interpreter is supplied, inspect that exact Python
    environment instead of FixPilot's own environment.
    """

    if not package_name:
        return {
            "name": package_name,
            "version": None,
            "installed": False,
        }

    # ---------------------------------------------------------
    # PROJECT INTERPRETER
    # ---------------------------------------------------------

    if interpreter:
        try:
            result = subprocess.run(
                [
                    str(interpreter),
                    "-c",
                    (
                        "import importlib.metadata as m; "
                        f"dist = m.distribution({package_name!r}); "
                        "print(dist.metadata.get('Name') or "
                        f"{package_name!r}); "
                        "print(dist.version)"
                    ),
                ],
                capture_output=True,
                text=True,
                timeout=15,
                shell=False,
            )

            if result.returncode == 0:
                lines = [
                    line.strip()
                    for line in result.stdout.splitlines()
                    if line.strip()
                ]

                if len(lines) >= 2:
                    return {
                        "name": lines[0],
                        "version": lines[1],
                        "installed": True,
                    }

                return {
                    "name": package_name,
                    "version": None,
                    "installed": True,
                }

            return {
                "name": package_name,
                "version": None,
                "installed": False,
            }

        except (
            OSError,
            subprocess.TimeoutExpired,
        ):
            return {
                "name": package_name,
                "version": None,
                "installed": False,
            }

    # ---------------------------------------------------------
    # FALLBACK: CURRENT FIXPILOT INTERPRETER
    # ---------------------------------------------------------

    try:
        distribution = metadata.distribution(
            package_name
        )

        return {
            "name": (
                distribution.metadata.get("Name")
                or package_name
            ),
            "version": distribution.version,
            "installed": True,
        }

    except metadata.PackageNotFoundError:
        return {
            "name": package_name,
            "version": None,
            "installed": False,
        }


def parse_requirements(path):
    path = Path(path)

    if not path.exists():
        return []

    packages = []

    for raw_line in path.read_text(
        encoding="utf-8",
        errors="ignore",
    ).splitlines():

        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        if line.startswith(
            ("-", "git+", "http:", "https:")
        ):
            continue

        line = line.split("#", 1)[0].strip()

        match = re.match(
            r"^([A-Za-z0-9_.-]+)\s*(.*)$",
            line,
        )

        if not match:
            continue

        name = match.group(1)
        specifier = match.group(2).strip()

        packages.append(
            {
                "name": name,
                "specifier": specifier,
            }
        )

    return packages


def parse_pyproject(path):
    path = Path(path)

    if not path.exists():
        return []

    text = path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    packages = []

    in_dependencies = False

    for line in text.splitlines():

        stripped = line.strip()

        if stripped.startswith("dependencies"):
            in_dependencies = True

        if in_dependencies:
            match = re.search(
                r"""["']([A-Za-z0-9_.-]+)\s*([<>=!~].*?)?["']""",
                stripped,
            )

            if match:
                packages.append(
                    {
                        "name": match.group(1),
                        "specifier": (
                            match.group(2) or ""
                        ).strip(),
                    }
                )

        if (
            in_dependencies
            and stripped.startswith("]")
        ):
            in_dependencies = False

    return packages


def parse_package_json(path):
    path = Path(path)

    if not path.exists():
        return {}

    try:
        data = json.loads(
            path.read_text(
                encoding="utf-8",
                errors="ignore",
            )
        )

    except (
        OSError,
        json.JSONDecodeError,
    ):
        return {}

    dependencies = {}

    for section in (
        "dependencies",
        "devDependencies",
        "optionalDependencies",
    ):
        values = data.get(section, {})

        if isinstance(values, dict):
            dependencies.update(values)

    return dependencies


def inspect_project_dependencies(project_root="."):
    root = Path(project_root).resolve()

    requirements = parse_requirements(
        root / "requirements.txt"
    )

    pyproject = parse_pyproject(
        root / "pyproject.toml"
    )

    package_json = parse_package_json(
        root / "package.json"
    )

    return {
        "python": {
            "requirements": requirements,
            "pyproject": pyproject,
        },
        "node": {
            "package_json": package_json,
        },
    }


def analyze_package(
    module_name,
    project_root=".",
    interpreter=None,
):
    """
    Analyze a Python package against the target project.

    The declaration comes from the project's dependency files.

    The installation state comes from the target project's
    Python interpreter.
    """

    package_name = import_to_package(
        module_name
    )

    installed = installed_package(
        package_name,
        interpreter=interpreter,
    )

    project = inspect_project_dependencies(
        project_root
    )

    declared = False
    declaration = None

    # ---------------------------------------------------------
    # requirements.txt
    # ---------------------------------------------------------

    for item in project["python"]["requirements"]:
        if (
            normalize_package_name(item["name"])
            == normalize_package_name(package_name)
        ):
            declared = True
            declaration = {
                **item,
                "source": "requirements.txt",
            }
            break

    # ---------------------------------------------------------
    # pyproject.toml
    # ---------------------------------------------------------

    if not declared:
        for item in project["python"]["pyproject"]:
            if (
                normalize_package_name(item["name"])
                == normalize_package_name(package_name)
            ):
                declared = True
                declaration = {
                    **item,
                    "source": "pyproject.toml",
                }
                break

    return {
        "module": module_name,
        "package": package_name,
        "installed": installed,
        "declared": declared,
        "declaration": declaration,
        "interpreter": interpreter,
    }