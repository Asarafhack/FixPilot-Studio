from __future__ import annotations

import hashlib
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


DEFAULT_IGNORED_DIRECTORIES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
}


@dataclass
class FileSnapshot:
    path: str
    size: int
    sha256: str

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProjectSnapshot:
    project_root: str
    files: list[FileSnapshot]
    file_count: int
    total_size: int
    fingerprint: str

    def as_dict(self) -> dict:
        return {
            "project_root": self.project_root,
            "files": [file.as_dict() for file in self.files],
            "file_count": self.file_count,
            "total_size": self.total_size,
            "fingerprint": self.fingerprint,
        }


class ProjectSnapshotter:
    """
    Creates a read-only fingerprint of project files.

    The snapshot does not modify project files.

    Ignored directories are excluded because folders such as node_modules,
    .git and virtual environments can contain thousands of generated files
    that are not useful for repair comparison.
    """

    def __init__(
        self,
        ignored_directories: Optional[set[str]] = None,
    ):
        self.ignored_directories = (
            set(ignored_directories)
            if ignored_directories is not None
            else set(DEFAULT_IGNORED_DIRECTORIES)
        )

    def create(self, project_root: str | Path) -> ProjectSnapshot:
        root = self._validate_project_root(project_root)

        files = []

        for path in self._iter_files(root):
            relative_path = path.relative_to(root)

            try:
                stat = path.stat()
                digest = self._sha256(path)
            except (OSError, PermissionError):
                continue

            files.append(
                FileSnapshot(
                    path=str(relative_path),
                    size=stat.st_size,
                    sha256=digest,
                )
            )

        files.sort(key=lambda item: item.path.lower())

        total_size = sum(item.size for item in files)
        fingerprint = self._fingerprint(files)

        return ProjectSnapshot(
            project_root=str(root),
            files=files,
            file_count=len(files),
            total_size=total_size,
            fingerprint=fingerprint,
        )

    def _iter_files(self, root: Path):
        for current_root, directories, filenames in __import__(
            "os"
        ).walk(root):
            directories[:] = [
                directory
                for directory in directories
                if directory not in self.ignored_directories
            ]

            for filename in filenames:
                path = Path(current_root) / filename

                if path.is_file():
                    yield path

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()

        with path.open("rb") as handle:
            while True:
                chunk = handle.read(1024 * 1024)

                if not chunk:
                    break

                digest.update(chunk)

        return digest.hexdigest()

    @staticmethod
    def _fingerprint(files: list[FileSnapshot]) -> str:
        digest = hashlib.sha256()

        for file in files:
            digest.update(file.path.encode("utf-8"))
            digest.update(b"\0")
            digest.update(str(file.size).encode("utf-8"))
            digest.update(b"\0")
            digest.update(file.sha256.encode("ascii"))
            digest.update(b"\0")

        return digest.hexdigest()

    @staticmethod
    def _validate_project_root(project_root: str | Path) -> Path:
        if not isinstance(project_root, (str, Path)):
            raise TypeError("project_root must be a string or Path")

        root = Path(project_root).expanduser().resolve()

        if not root.exists():
            raise FileNotFoundError(
                f"project root does not exist: {root}"
            )

        if not root.is_dir():
            raise NotADirectoryError(
                f"project root is not a directory: {root}"
            )

        return root


def create_project_snapshot(
    project_root: str | Path,
) -> dict:
    """
    Convenience API returning a serializable snapshot.
    """
    snapshotter = ProjectSnapshotter()
    return snapshotter.create(project_root).as_dict()