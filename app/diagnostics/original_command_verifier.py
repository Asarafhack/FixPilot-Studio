from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Optional, Sequence

from app.diagnostics.reproducer import FailureReproducer


@dataclass
class OriginalCommandVerification:
    command: list[str]
    project_root: str
    success: bool
    exit_code: Optional[int]
    output: str
    stdout: str
    stderr: str
    timed_out: bool
    duration_seconds: float
    failure_resolved: bool

    def as_dict(self) -> dict:
        return asdict(self)


class OriginalCommandVerifier:
    """
    Re-runs the exact original command after a repair.

    The command is executed through FailureReproducer, which guarantees:
    - shell=False
    - explicit argument lists
    - project-root validation
    - timeout protection
    """

    def __init__(self, timeout: int = 30):
        self.reproducer = FailureReproducer(timeout=timeout)

    def verify(
        self,
        command: Sequence[str],
        project_root: str,
        timeout: Optional[int] = None,
    ) -> OriginalCommandVerification:
        result = self.reproducer.reproduce(
            command=command,
            project_root=project_root,
            timeout=timeout,
        )

        return OriginalCommandVerification(
            command=result.command,
            project_root=result.project_root,
            success=result.success,
            exit_code=result.exit_code,
            output=result.combined_output,
            stdout=result.stdout,
            stderr=result.stderr,
            timed_out=result.timed_out,
            duration_seconds=result.duration_seconds,
            failure_resolved=result.success,
        )


def verify_original_command(
    command: Sequence[str],
    project_root: str,
    timeout: int = 30,
) -> dict:
    """
    Convenience API returning a serializable verification result.
    """

    verifier = OriginalCommandVerifier(timeout=timeout)

    return verifier.verify(
        command=command,
        project_root=project_root,
    ).as_dict()