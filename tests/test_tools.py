from tools.registry import TOOLS, run_tool, tool_specs

def test_registry_populated():
    assert len(TOOLS) >= 15
    assert "wifi_scan" in TOOLS and "remember" in TOOLS

def test_unknown_tool():
    assert "[unknown-tool]" in run_tool("nope", {})

def test_specs_shape():
    for s in tool_specs():
        assert {"name", "description", "args"} <= set(s)

def test_files_sandbox():
    out = run_tool("read_file", {"path": "../../../etc/passwd"})
    assert "[error]" in out or "PermissionError" in out
