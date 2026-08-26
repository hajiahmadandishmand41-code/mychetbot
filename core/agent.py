"""Compatibility facade for the unified conversational agent.

The implementation lives in :mod:`core.agent_impl` so the public import path
remains stable while planner behavior can be tested independently.
"""

from core.agent_impl import Agent, SYSTEM_PROMPT, TOOL_PLANNER_PROMPT

__all__ = ["Agent", "SYSTEM_PROMPT", "TOOL_PLANNER_PROMPT"]
