from core.agent import Agent
from core.config import config


def test_ordinary_chat_skips_tool_planner():
    assert Agent._needs_tool_planner("سلام، حالت چطوره؟") is False
    assert Agent._needs_tool_planner("برای من یک داستان کوتاه بنویس") is False


def test_tool_queries_still_use_planner():
    assert Agent._needs_tool_planner("آخرین اخبار امروز را پیدا کن") is True
    assert Agent._needs_tool_planner("این URL را بررسی کن: https://example.com") is True
    assert Agent._needs_tool_planner("وضعیت وای فای را بررسی کن") is True


def test_resilient_model_defaults():
    assert config.default_model == "auto/bynara"
    assert "agnes-2.5-flash" in config.nara_fallback_models
