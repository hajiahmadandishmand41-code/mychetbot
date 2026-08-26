from fastapi.testclient import TestClient

from interfaces.api_server import app


client = TestClient(app)


def test_health_is_public_and_chat_only():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "chat_provider" not in body
    assert "tools" not in body


def test_chat_requires_api_token(monkeypatch):
    from core.config import config

    monkeypatch.setattr(config, "api_token", "test-token")
    response = client.post("/chat", json={"message": "سلام", "session": "s"})
    assert response.status_code == 401


def test_history_and_memory_delete_are_protected(monkeypatch):
    from core.config import config

    monkeypatch.setattr(config, "api_token", "test-token")
    headers = {"Authorization": "Bearer test-token"}
    assert client.get("/history/s", headers=headers).status_code == 200
    assert client.delete("/memory/s", headers=headers).status_code == 200


def test_api_session_is_bound_to_auth_principal(monkeypatch):
    from interfaces import api_server
    from core.config import config

    monkeypatch.setattr(config, "api_token", "token-a")
    assert api_server._owned_session("shared", "token-a") != api_server._owned_session("shared", "token-b")
