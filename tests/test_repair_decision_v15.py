from app.repair.decision import build_repair_decision


def test_build_repair_decision():
    result = build_repair_decision(
        action="pip_install",
        reason="The required Python dependency is missing.",
        evidence=[
            "Import failed.",
            "Dependency is not installed.",
        ],
        risk_level="low",
        requires_approval=True,
        verification_method="Re-run the original command.",
        target="flask",
        confidence=0.95,
    )

    assert result["action"] == "pip_install"
    assert result["reason"] == (
        "The required Python dependency is missing."
    )
    assert result["risk_level"] == "low"
    assert result["requires_approval"] is True
    assert result["target"] == "flask"
    assert result["confidence"] == 0.95


def test_decision_is_serializable():
    result = build_repair_decision(
        action="verify_import",
        reason="Verify that the dependency can be imported.",
        evidence=[
            "Repair was completed.",
        ],
        risk_level="low",
        requires_approval=False,
        verification_method="Import the module.",
    )

    assert isinstance(result, dict)
    assert isinstance(result["evidence"], list)


def test_rejects_empty_action():
    try:
        build_repair_decision(
            action="",
            reason="test",
            evidence=[],
        )
    except ValueError as exc:
        assert "action" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_rejects_empty_reason():
    try:
        build_repair_decision(
            action="pip_install",
            reason="",
            evidence=[],
        )
    except ValueError as exc:
        assert "reason" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_rejects_invalid_risk_level():
    try:
        build_repair_decision(
            action="pip_install",
            reason="Install dependency.",
            evidence=[],
            risk_level="critical",
        )
    except ValueError as exc:
        assert "risk_level" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_rejects_invalid_confidence():
    try:
        build_repair_decision(
            action="pip_install",
            reason="Install dependency.",
            evidence=[],
            confidence=1.5,
        )
    except ValueError as exc:
        assert "confidence" in str(exc)
    else:
        raise AssertionError(
            "Expected ValueError."
        )


def test_requires_approval_can_be_disabled():
    result = build_repair_decision(
        action="verify_import",
        reason="Verification only.",
        evidence=[
            "No modification is performed.",
        ],
        requires_approval=False,
    )

    assert result["requires_approval"] is False