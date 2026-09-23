from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Sequence


@dataclass
class OriginalCommand:
    command: list[str]
    project_root: str
    source: str = "user"
    description: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


class OriginalCommandCapture:
    """
    Stores the exact command FixPilot should reproduce and verify later.

    The command is represented as argument tokens rather than a shell string.
    This keeps the command compatible with shell=False execution.
    """

    def capture(
        self,
        command: Sequence[str],
        project_root: str | Path,
        source: str = "user",
        description: str = "",
    ) -> OriginalCommand:
        validated_command = self._validate_command(command)
        root = self._validate_project_root(project_root)

        if not isinstance(source, str) or not source.strip():
            raise ValueError("source must be a non-empty string")

        if not isinstance(description, str):
            raise TypeError("description must be a string")

        return OriginalCommand(
            command=validated_command,
            project_root=str(root),
            source=source.strip(),
            description=description.strip(),
        )

    @staticmethod
    def _validate_command(command: Sequence[str]) -> list[str]:
        if isinstance(command, (str, bytes)):
            raise TypeError(
                "command must be a sequence of arguments, not a shell string"
            )

        if not isinstance(command, Sequence):
            raise TypeError("command must be a sequence of arguments")

        if not command:
            raise ValueError("command cannot be empty")

        result = []

        for index, argument in enumerate(command):
            if not isinstance(argument, str):
                raise TypeError(
                    f"command argument {index} must be a string"
                )

            if not argument:
                raise ValueError(
                    f"command argument {index} cannot be empty"
                )

            result.append(argument)

        return result

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


def capture_original_command(
    command: Sequence[str],
    project_root: str | Path,
    source: str = "user",
    description: str = "",
) -> dict:
    """
    Convenience API returning a serializable command record.
    """
    capture = OriginalCommandCapture()

    return capture.capture(
        command=command,
        project_root=project_root,
        source=source,
        description=description,
    ).as_dict()