from __future__ import annotations

import json

from tools.wifi_tool import _band, _channel, _security, _wps, capability_detection
from tools.registry import TOOLS


def test_security_classifier():
    assert _security("[WPA2-PSK-CCMP][ESS]") == "WPA2"
    assert _security("[WPA3-SAE-CCMP][ESS]") == "WPA3-Personal"
    assert _security("[WEP][ESS]") == "WEP"
    assert _security("[ESS]") == "Open-or-Unknown"
    assert _security("") == "Unknown"


def test_wps_is_not_faked():
    assert _wps("[WPA2-PSK-CCMP][WPS][ESS]") == "advertised"
    assert _wps("[WPA2-PSK-CCMP][ESS]") == "not-advertised"
    assert _wps("") == "unknown"


def test_channel_and_band():
    assert _channel(2412) == 1
    assert _channel(5180) == 36
    assert _channel(5955) == 1
    assert _band(2412) == "2.4 GHz"
    assert _band(5180) == "5 GHz"
    assert _band(5955) == "6 GHz"


def test_registry_exposes_audit_tools():
    for name in ("wifi_capabilities", "wifi_scan", "wifi_info", "wifi_diagnostics", "wifi_security_report"):
        assert name in TOOLS
        assert TOOLS[name].dangerous is False


def test_capability_output_is_json_and_declares_blocked_operations():
    data = json.loads(capability_detection())
    assert data["mode"] == "legal_security_audit"
    assert "WPS PIN attacks" in data["unsupported_or_intentionally_blocked"]
    assert data["root_required_for_audit"] is False
