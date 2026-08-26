import os
import tempfile
from pathlib import Path

from agent.core.security import PermissionLevel, check
from agent.memory.store import MemoryStore
from agent.tools.builtin import build_tools


def test_permission_levels():
    assert check("ping", {}).level == PermissionLevel.SAFE
    assert check("network_scan", {}).requires_confirmation
    assert not check("credential_theft", {}).allowed
    assert check("wifite_tool", {}).requires_confirmation


def test_memory_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        store = MemoryStore(d)
        store.save("note", "wifi lab uses router-a")
        assert "router-a" in store.search("router-a", 1)[0]["content"]


def test_files_and_wifi_tools_are_registered():
    with tempfile.TemporaryDirectory() as d:
        tools = build_tools(MemoryStore(d))
        required = {"list_files", "read_file", "write_file", "delete_file", "terminal", "wifi_manager", "network_info", "connectivity", "ping", "dns_lookup", "network_scan", "wifite_detect", "wifite_tool", "system_info", "battery", "storage_info", "zip_info", "zip_extract"}
        assert required.issubset(tools)


def test_wifite_detection_is_non_fatal():
    with tempfile.TemporaryDirectory() as d:
        result = build_tools(MemoryStore(d))["wifite_detect"]({})
        assert "installed" in result
        assert "message" in result


def test_zip_tools_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        source = root / "hello.txt"
        source.write_text("hello", encoding="utf-8")
        archive = root / "a.zip"
        import zipfile
        with zipfile.ZipFile(archive, "w") as zf:
            zf.write(source, "hello.txt")
        tools = build_tools(MemoryStore(d))
        assert tools["zip_info"]({"path": str(archive)})["count"] == 1
        out = root / "out"
        tools["zip_extract"]({"path": str(archive), "destination": str(out)})
        assert (out / "hello.txt").read_text(encoding="utf-8") == "hello"
