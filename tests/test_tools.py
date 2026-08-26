import pytest

from tools.files_tool import read_file, write_file
from tools.registry import TOOLS, run_tool, tool_specs


def test_registry_populated():
    assert len(TOOLS) >= 15
    assert "wifi_scan" in TOOLS and "remember" in TOOLS


def test_unknown_tool():
    result = run_tool("nope", {})
    assert "unknown_tool" in result


def test_specs_shape_and_security_metadata():
    for spec in tool_specs():
        assert {"name", "description", "input_schema", "risk_level", "permission_scope", "runtime_requirements", "timeout", "availability", "result_schema", "auto_selectable"} <= set(spec)
    assert TOOLS["shell"].auto_selectable is False
    assert TOOLS["write_file"].risk_level == "high"


def test_dangerous_tools_require_confirmation():
    result = run_tool("write_file", {"path": "README.md", "content": "do not execute"})
    assert "permission_required" in result


def test_files_sandbox():
    out = run_tool("read_file", {"path": "../../../etc/passwd"})
    assert "[error]" in out or "PermissionError" in out


def test_secret_paths_are_not_readable_or_writable():
    with pytest.raises(PermissionError):
        read_file(".env")
    with pytest.raises(PermissionError):
        read_file(".env.production")
    with pytest.raises(PermissionError):
        write_file(".env", "SECRET=value")


def test_server_profile_blocks_local_capabilities():
    assert "capability_unavailable" in run_tool("shell", {"command": "pwd"}, profile="server")
    assert "capability_unavailable" in run_tool("read_file", {"path": "README.md"}, profile="server")
    assert "capability_unavailable" in run_tool("wifi_scan", {}, profile="server")
    assert "remember" in {item["name"] for item in tool_specs("server")}


def test_local_profile_does_not_require_android():
    assert "wifi_scan" not in {item["name"] for item in tool_specs("local")}
