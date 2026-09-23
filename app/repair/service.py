from app.repair.approval import (
    approve_repair,
    create_approval_request,
)
from app.repair.executor import execute_plan
from app.repair.verifier import verify_plan


def _is_verification_action(action):
    return action in {
        "verify_import",
        "verify_environment",
        "inspect_port",
        "inspect_path",
    }


def _is_noop_install(package, cwd=None):
    """
    Return True when a Python package is already importable.
    """

    if not package:
        return False

    from app.repair.verifier import verify_python_import

    result = verify_python_import(package)

    return result.get("success") is True


def repair_and_verify(
    plan,
    cwd=None,
    original_command=None,
    approved=False,
):
    """
    Execute and verify a structured repair plan.

    Modification actions require explicit approval.

    Read-only verification actions do not require approval.

    Flow:

        Plan
          ↓
        Safety Validator
          ↓
        Approval Gate
          ↓
        Executor
          ↓
        Verification
    """

    if not plan:
        return {
            "success": False,
            "stage": "planning",
            "message": "No repair plan is available.",
        }

    execution_results = []

    for item in plan:
        action = item.get("action")

        # -----------------------------------------------------
        # Approval gate
        # -----------------------------------------------------

        approval_request = create_approval_request(item)

        if approval_request.get("required"):

            if not approved:
                return {
                    "success": False,
                    "stage": "approval_required",
                    "message": approval_request["message"],
                    "approval_request": approval_request,
                    "execution_results": execution_results,
                    "verification": None,
                }

            approval = approve_repair(
                approval_request
            )

            if not approval.get("approved"):
                return {
                    "success": False,
                    "stage": "approval_denied",
                    "message": "Repair was not approved.",
                    "approval_request": approval_request,
                    "execution_results": execution_results,
                    "verification": None,
                }

        # -----------------------------------------------------
        # Skip unnecessary Python installation.
        # -----------------------------------------------------

        if action == "pip_install":
            package = item.get("package")

            if _is_noop_install(
                package,
                cwd=cwd,
            ):
                execution = {
                    "success": True,
                    "blocked": False,
                    "action": action,
                    "package": package,
                    "skipped": True,
                    "message": (
                        f"Package '{package}' is already "
                        "available. Installation skipped."
                    ),
                }

                execution_results.append(execution)
                continue

        # -----------------------------------------------------
        # Execute
        # -----------------------------------------------------

        execution = execute_plan(
            item,
            cwd=cwd,
        )

        execution_results.append(execution)

        if not execution.get("success"):

            if _is_verification_action(action):
                continue

            return {
                "success": False,
                "stage": "execution",
                "message": execution.get(
                    "message",
                    "Repair execution failed.",
                ),
                "execution_results": execution_results,
                "verification": None,
            }

    # ---------------------------------------------------------
    # Verification
    # ---------------------------------------------------------

    verification = verify_plan(
        plan,
        execution_results,
        cwd=cwd,
        original_command=original_command,
    )

    if not verification.get("success"):
        return {
            "success": False,
            "stage": "verification",
            "message": verification.get(
                "message",
                "Repair verification failed.",
            ),
            "execution_results": execution_results,
            "verification": verification,
        }

    return {
        "success": True,
        "stage": "completed",
        "message": "Repair executed and verified successfully.",
        "execution_results": execution_results,
        "verification": verification,
    }