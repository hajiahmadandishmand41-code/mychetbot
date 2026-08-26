import pytest
from fastapi import HTTPException

from core.config import config
from interfaces.api_server import ChatIn, _SESSION_RE, _auth, _rate_limit_key
from tools.registry import tool_specs


def test_session_validation():
    assert _SESSION_RE.fullmatch("tg:12345")
    assert not _SESSION_RE.fullmatch("bad/session")


def test_chat_input_rejects_blank_message():
    with pytest.raises(ValueError):
        ChatIn(message="   ")


def test_auth_uses_constant_time_compare(monkeypatch):
    monkeypatch.setattr(config, "api_token", "secret-token")
    with pytest.raises(HTTPException) as exc:
        _auth("Bearer wrong-token")
    assert exc.value.status_code == 401


def test_server_api_tool_profile_exposes_only_safe_tools(monkeypatch):
    monkeypatch.setattr(config, "api_tool_profile", "server")
    names = {item["name"] for item in tool_specs(config.api_tool_profile)}
    assert "remember" in names
    assert "shell" not in names
    assert "read_file" not in names
    assert "wifi_scan" not in names


def test_forwarded_for_is_not_trusted_by_default(monkeypatch):
    monkeypatch.setattr(config, "trust_proxy", False)
    body = ChatIn(message="hello", session="s")

    class Client:
        host = "10.0.0.5"

    class Request:
        client = Client()
        headers = {"x-forwarded-for": "203.0.113.10"}

    assert _rate_limit_key(body, Request()).startswith("10.0.0.5:")
