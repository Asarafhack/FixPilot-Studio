from app.repair.approval import (
    approve_repair,
    create_approval_request,
    requires_approval,
)


def test_pip_install_requires_approval():
    plan = {
        "action": "pip_install",
        "package": "flask",
        "risk": "LOW",
    }

    assert requires_approval(plan) is True


def test_npm_install_requires_approval():
    plan = {
        "action": "npm_install",
        "package": "express",
        "risk": "LOW",
    }

    assert requires_approval(plan) is True


def test_verify_import_does_not_require_approval():
    plan = {
        "action": "verify_import",
        "package": "flask",
        "risk": "LOW",
    }

    assert requires_approval(plan) is False


def test_approval_request_is_not_approved_by_default():
    plan = {
        "action": "pip_install",
        "package": "flask",
        "risk": "LOW",
    }

    request = create_approval_request(plan)

    assert request["required"] is True
    assert request["approved"] is False
    assert request["action"] == "pip_install"


def test_user_can_approve_repair():
    plan = {
        "action": "pip_install",
        "package": "flask",
        "risk": "LOW",
    }

    request = create_approval_request(plan)
    approved = approve_repair(request)

    assert approved["approved"] is True
    assert approved["action"] == "pip_install"


def test_invalid_plan_does_not_require_approval():
    assert requires_approval(None) is False