import pytest
from fastapi import HTTPException

from core.config import config
from interfaces.api_server import _SESSION_RE, ChatIn, _auth


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
