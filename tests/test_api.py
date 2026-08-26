from fastapi.testclient import TestClient

from interfaces.api_server import app


client = TestClient(app)


def test_health_is_public_and_provider_independent():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_protected_tools_require_api_token(monkeypatch):
    from core.config import config

    monkeypatch.setattr(config, "api_token", "test-token")
    response = client.get("/tools")
    assert response.status_code == 401
    response = client.get("/tools", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200
    assert response.json()["profile"] == config.api_tool_profile
