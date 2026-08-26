from pathlib import Path

from tools.files_tool import write_file
from tools.registry import TOOLS, run_tool, tool_specs


def test_registry_populated():
    assert len(TOOLS) >= 15
    assert "wifi_scan" in TOOLS and "remember" in TOOLS


def test_unknown_tool():
    assert "[unknown-tool]" in run_tool("nope", {})


def test_specs_shape():
    for spec in tool_specs():
        assert {"name", "description", "args"} <= set(spec)


def test_files_sandbox():
    out = run_tool("read_file", {"path": "../../../etc/passwd"})
    assert "[error]" in out or "PermissionError" in out


def test_secret_paths_are_not_writable(tmp_path: Path):
    try:
        write_file(".env", "SECRET=value")
    except PermissionError:
        pass
    else:
        raise AssertionError("Agent must not write .env")

    assert not (tmp_path / ".env").exists()
