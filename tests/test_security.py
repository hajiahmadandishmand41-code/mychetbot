from core.config import config
from core.security import decrypt, encrypt, is_command_allowed, redact


def test_shell_blocked_by_default(monkeypatch):
    monkeypatch.setattr(config, "allow_shell", False)
    assert is_command_allowed("ls")[0] is False


def test_dangerous_and_shell_syntax_blocked(monkeypatch):
    monkeypatch.setattr(config, "allow_shell", True)
    monkeypatch.setattr(config, "shell_whitelist", ["rm", "ls"])
    assert is_command_allowed("rm -rf /")[0] is False
    assert is_command_allowed("ls; whoami")[0] is False
    assert is_command_allowed("ls > out")[0] is False


def test_whitelist(monkeypatch):
    monkeypatch.setattr(config, "allow_shell", True)
    monkeypatch.setattr(config, "shell_whitelist", ["ls"])
    assert is_command_allowed("ls -la")[0] is True
    assert is_command_allowed("curl x")[0] is False


def test_crypto_roundtrip():
    assert decrypt(encrypt("secret")) == "secret"


def test_redact():
    output = redact("key sk-abcdefgh12345 BSSID AA:BB:CC:DD:EE:FF")
    assert "sk-abcdefgh12345" not in output
    assert "AA:BB:CC:xx:xx:xx" in output
