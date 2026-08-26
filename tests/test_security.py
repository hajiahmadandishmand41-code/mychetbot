from agent.core.security import check


def test_read_is_safe():
    d = check('read_file', {'path': 'x'})
    assert d.allowed and not d.requires_confirmation


def test_terminal_requires_confirmation():
    d = check('terminal', {'command': 'echo ok'})
    assert d.allowed and d.requires_confirmation


def test_unknown_is_denied():
    assert not check('unknown', {}).allowed
