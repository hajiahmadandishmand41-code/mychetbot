# Security Testing (Isolated)

For defensive testing, use simulation rather than bypassing a real security control.

The repository's security test harness can model:

- denied Android permissions;
- disabled Accessibility capability;
- unavailable Termux execution capability;
- unauthenticated sessions;
- CAPTCHA not completed.

A simulated denial must remain a denial. The test suite must never turn a failed
real authentication, CAPTCHA, or Android permission check into authorization.

For stronger testing, connect these decisions to mock services or local fixtures
that reproduce the expected failure modes without sending bypass attempts to a
third-party service.
