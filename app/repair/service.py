from app.repair.executor import execute_plan
from app.repair.verifier import verify_plan


def repair_and_verify(
    plan,
    cwd=None,
    original_command=None,
):
    """
    Execute a structured repair plan and automatically verify it.

    Execution actions perform changes.

    Verification actions perform checks.

    A failed verification must be reported as a
    verification failure, not an execution failure.
    """

    if not plan:
        return {
            "success": False,
            "stage": "planning",
            "message": "No repair plan is available.",
        }

    execution_results = []

    verification_actions = {
        "verify_import",
        "verify_environment",
        "inspect_port",
        "inspect_path",
    }

    # ---------------------------------------------------------
    # Execute each plan item.
    # ---------------------------------------------------------

    for item in plan:
        action = item.get("action")

        execution = execute_plan(
            item,
            cwd=cwd,
        )

        execution_results.append(execution)

        # A verification action can legitimately return
        # success=False because the condition being checked
        # was not satisfied.
        #
        # It must therefore continue to the verification
        # stage instead of being classified as an executor
        # failure.
        if not execution.get("success"):
            if action in verification_actions:
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

    # ---------------------------------------------------------
    # Completed successfully.
    # ---------------------------------------------------------

    return {
        "success": True,
        "stage": "completed",
        "message": "Repair executed and verified successfully.",
        "execution_results": execution_results,
        "verification": verification,
    }