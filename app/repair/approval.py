class ApprovalRequired(Exception):
    """Raised when a repair requires explicit user approval."""


def requires_approval(plan):
    """
    Return True when a repair plan contains an action
    that can modify the developer environment.
    """

    if not isinstance(plan, dict):
        return False

    action = plan.get("action")

    return action in {
        "pip_install",
        "npm_install",
        "declare_dependency",
    }


def create_approval_request(plan):
    """
    Create a structured approval request.

    This function does not execute anything.
    """

    if not isinstance(plan, dict):
        return {
            "required": False,
            "approved": False,
            "message": "Invalid repair plan.",
        }

    action = plan.get("action")
    package = plan.get("package")

    if not requires_approval(plan):
        return {
            "required": False,
            "approved": True,
            "action": action,
            "package": package,
            "message": "No user approval is required.",
        }

    return {
        "required": True,
        "approved": False,
        "action": action,
        "package": package,
        "risk": plan.get("risk", "UNKNOWN"),
        "message": (
            f"FixPilot wants to execute '{action}'"
            + (
                f" for package '{package}'."
                if package
                else "."
            )
            + " User approval is required."
        ),
    }


def approve_repair(request):
    """
    Explicitly approve a previously generated request.

    The caller must provide the approval request itself.
    """

    if not isinstance(request, dict):
        return {
            "approved": False,
            "message": "Invalid approval request.",
        }

    if not request.get("required"):
        return {
            "approved": True,
            "message": "Approval was not required.",
        }

    return {
        **request,
        "approved": True,
        "message": "Repair approved by user.",
    }