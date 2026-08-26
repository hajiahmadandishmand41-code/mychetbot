from __future__ import annotations

import json

from core.config import config
from tools.registry import run_tool, tool_specs


def test_server_execute_denied_without_permission() -> None:
    previous_enabled = config.server_execution_enabled
    previous_profile = config.tool_profile
    previous_sessions = config.server_exec_allowed_sessions
    previous_allowlist = config.server_exec_allowlist
    try:
        config.server_execution_enabled = True
        config.tool_profile = "server"
        config.server_exec_allowed_sessions = ("admin-session",)
        config.server_exec_allowlist = ("server_execute",)
        result = json.loads(run_tool("server_execute", {"operation": "health", "path": ".", "script": "", "timeout": 2}, profile="server", session="normal-session"))
        assert result["status"] == "denied"
    finally:
        config.server_execution_enabled = previous_enabled
        config.tool_profile = previous_profile
        config.server_exec_allowed_sessions = previous_sessions
        config.server_exec_allowlist = previous_allowlist


def test_server_tool_metadata_exposes_limits() -> None:
    names = {item["name"]: item for item in tool_specs("server")}
    assert "server_diagnostics" in names
    assert names["server_diagnostics"]["memory_limit_mb"] > 0
    assert names["server_diagnostics"]["process_limit"] > 0
    assert names["server_diagnostics"]["output_limit_chars"] > 0
    assert "working_directory" in names["server_diagnostics"]
    assert "allowed_environment" in names["server_diagnostics"]
