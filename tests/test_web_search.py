from __future__ import annotations

import json

from tools import web_search


def test_search_result_url_unwrap() -> None:
    raw = "https://html.duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage"
    assert web_search._unwrap_result_url(raw) == "https://example.com/page"


def test_topic_search_dispatches(monkeypatch) -> None:
    monkeypatch.setattr(web_search.config, "web_enabled", True)
    monkeypatch.setattr(web_search, "_search_engine", lambda query: [{"title": "Example", "url": "https://example.com", "snippet": "snippet"}])
    monkeypatch.setattr(web_search, "_fetch", lambda url: ("<html><title>Example</title><body>Useful data</body></html>", 200, url, 66, "text/html"))
    result = json.loads(web_search.search_and_research("latest information about example"))
    assert result["status"] == "success"
    assert result["data"]["results"][0]["page"]["title"] == "Example"
    assert "Useful data" in result["data"]["results"][0]["page"]["text"]


def test_url_research_dispatches_without_search(monkeypatch) -> None:
    monkeypatch.setattr(web_search.config, "web_enabled", True)
    called = {"search": False}
    monkeypatch.setattr(web_search, "_search_engine", lambda query: called.__setitem__("search", True) or [])
    monkeypatch.setattr(web_search, "_validate_url", lambda url: url)
    monkeypatch.setattr(web_search, "_fetch", lambda url: ("<html><title>Example</title><body>Direct data</body></html>", 200, url, 65, "text/html"))
    result = json.loads(web_search.search_and_research("https://example.com"))
    assert result["status"] == "success"
    assert not called["search"]
    assert result["data"]["pages"][0]["title"] == "Example"
