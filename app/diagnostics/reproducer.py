from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Sequence


@dataclass
class ReproductionResult:
    command: list[str]
    project_root: str
    success: bool
    exit_code: Optional[int]
    stdout: str
    stderr: str
    combined_output: str
    duration_seconds: float
    timed_out: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


class FailureReproducer:
    """
    Safely reproduces a project failure by running an explicit command.

    Security rules:
    - shell=False is always used.
    - The command must be a sequence of arguments.
    - The project root must exist and be a directory.
    - No arbitrary shell string is accepted.
    - A timeout prevents hung processes.
    """

    def __init__(self, timeout: int = 30):
        if not isinstance(timeout, int) or timeout <= 0:
            raise ValueError("timeout must be a positive integer")

        self.timeout = timeout

    def reproduce(
        self,
        command: Sequence[str],
        project_root: str | Path,
        timeout: Optional[int] = None,
    ) -> ReproductionResult:
        validated_command = self._validate_command(command)
        root = self._validate_project_root(project_root)

        effective_timeout = self.timeout if timeout is None else timeout

        if not isinstance(effective_timeout, int) or effective_timeout <= 0:
            raise ValueError("timeout must be a positive integer")

        started = time.perf_counter()

        try:
            completed = subprocess.run(
                validated_command,
                cwd=str(root),
                shell=False,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                check=False,
            )

            duration = time.perf_counter() - started

            stdout = completed.stdout or ""
            stderr = completed.stderr or ""

            return ReproductionResult(
                command=validated_command,
                project_root=str(root),
                success=completed.returncode == 0,
                exit_code=completed.returncode,
                stdout=stdout,
                stderr=stderr,
                combined_output=self._combine_output(stdout, stderr),
                duration_seconds=round(duration, 6),
                timed_out=False,
            )

        except subprocess.TimeoutExpired as exc:
            duration = time.perf_counter() - started

            stdout = self._decode_output(exc.stdout)
            stderr = self._decode_output(exc.stderr)

            return ReproductionResult(
                command=validated_command,
                project_root=str(root),
                success=False,
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                combined_output=self._combine_output(stdout, stderr),
                duration_seconds=round(duration, 6),
                timed_out=True,
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

        validated: list[str] = []

        for index, argument in enumerate(command):
            if not isinstance(argument, str):
                raise TypeError(
                    f"command argument {index} must be a string"
                )

            if not argument:
                raise ValueError(
                    f"command argument {index} cannot be empty"
                )

            validated.append(argument)

        return validated

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

    @staticmethod
    def _combine_output(stdout: str, stderr: str) -> str:
        parts = []

        if stdout:
            parts.append(stdout.rstrip())

        if stderr:
            parts.append(stderr.rstrip())

        return "\n".join(parts)

    @staticmethod
    def _decode_output(value) -> str:
        if value is None:
            return ""

        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")

        return str(value)


def reproduce_failure(
    command: Sequence[str],
    project_root: str | Path,
    timeout: int = 30,
) -> dict:
    """
    Convenience API used by higher-level FixPilot services.
    """
    reproducer = FailureReproducer(timeout=timeout)
    return reproducer.reproduce(
        command=command,
        project_root=project_root,
    ).as_dict()