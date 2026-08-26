from core.security import is_command_allowed, encrypt, decrypt, redact
from core.config import config

def test_shell_blocked_by_default(monkeypatch):
    monkeypatch.setattr(config, "allow_shell", False)
    ok, _ = is_command_allowed("ls")
    assert ok is False

def test_dangerous_blocked(monkeypatch):
    monkeypatch.setattr(config, "allow_shell", True)
    monkeypatch.setattr(config, "shell_whitelist", ["rm"])
    ok, _ = is_command_allowed("rm -rf /")
    assert ok is False

def test_whitelist(monkeypatch):
    monkeypatch.setattr(config, "allow_shell", True)
    monkeypatch.setattr(config, "shell_whitelist", ["ls"])
    assert is_command_allowed("ls -la")[0] is True
    assert is_command_allowed("curl x")[0] is False

def test_crypto_roundtrip():
    assert decrypt(encrypt("secret")) == "secret"

def test_redact():
    assert "sk-***" in redact("key sk-abcdefgh12345")
