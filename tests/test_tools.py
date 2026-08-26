import json

from tools.registry import TOOLS, run_tool, tool_specs


def test_registry_populated():
    assert len(TOOLS) >= 15
    assert "wifi_scan" in TOOLS and "remember" in TOOLS


def test_unknown_tool():
    assert "unknown_tool" in run_tool("nope", {})


def test_specs_shape():
    for spec in tool_specs():
        assert {"name", "description", "args"} <= set(spec)


def test_files_sandbox():
    out = run_tool("read_file", {"path": "../../../etc/passwd"})
    assert "[error]" in out or "PermissionError" in out


def test_server_profile_separates_device_capabilities():
    payload = json.loads(run_tool("wifi_scan", {}, profile="server"))
    assert payload["error"] == "capability_unavailable"
    assert payload["tool"] == "wifi_scan"
    assert "wifi_scan" not in {spec["name"] for spec in tool_specs("server")}
    assert "remember" in {spec["name"] for spec in tool_specs("server")}
