"""Isolated security-boundary simulations.

These tests model denied authentication/CAPTCHA/permission scenarios locally.
They never contact a real service and never bypass a real control.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    allowed: bool
    reason: str


def authorize(capability: str, granted: bool) -> Decision:
    if granted:
        return Decision(True, f"capability granted: {capability}")
    return Decision(False, f"capability denied: {capability}")


def test_permission_boundary_denies_when_not_granted():
    result = authorize("android.accessibility", granted=False)
    assert result.allowed is False
    assert "denied" in result.reason


def test_permission_boundary_allows_only_explicit_grant():
    result = authorize("termux.run_command", granted=True)
    assert result.allowed is True


def test_authentication_bypass_is_not_modelled_as_success():
    result = authorize("authenticated-session", granted=False)
    assert result.allowed is False


def test_captcha_bypass_is_not_modelled_as_success():
    result = authorize("captcha-passed", granted=False)
    assert result.allowed is False
