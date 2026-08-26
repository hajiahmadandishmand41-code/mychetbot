"""Central safety policy for MyChatBot tools."""
from dataclasses import dataclass
from enum import Enum


class PermissionLevel(str, Enum):
    SAFE = "SAFE"
    CONFIRM = "CONFIRM"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class Decision:
    allowed: bool
    level: PermissionLevel
    requires_confirmation: bool = False
    reason: str = ""


SAFE_TO_AUTO_RUN = {
    "list_files", "read_file", "memory_search", "memory_save",
    "zip_info", "zip_extract", "wifi_manager", "network_info",
    "connectivity", "ping", "dns_lookup", "traceroute", "system_info",
    "battery", "storage_info", "wifi_interface_info", "wifite_detect",
}

CONFIRM = {
    "write_file", "delete_file", "terminal", "network_scan", "wifite_tool",
    "clipboard_write", "send_notification", "wifi_scan",
}

BLOCKED = {
    "credential_theft", "unauthorized_access", "third_party_attack",
    "deauth_attack", "password_cracking", "token_exfiltration",
}


def check(tool_name: str, arguments: dict) -> Decision:
    if tool_name in BLOCKED:
        return Decision(False, PermissionLevel.BLOCKED, False, "This operation is blocked by the security policy.")
    if tool_name in SAFE_TO_AUTO_RUN:
        return Decision(True, PermissionLevel.SAFE)
    if tool_name in CONFIRM:
        return Decision(True, PermissionLevel.CONFIRM, True, "This operation can change device state, access active network services, or launch a security tool and requires explicit user confirmation.")
    return Decision(False, PermissionLevel.BLOCKED, False, f"Unknown tool '{tool_name}' is not permitted.")
