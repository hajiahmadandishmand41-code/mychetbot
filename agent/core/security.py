"""Safety and permission policy for MyChatBot tools."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    allowed: bool
    requires_confirmation: bool = False
    reason: str = ""


# Conservative by default. Extend through policy, never by silently bypassing it.
SAFE_TO_AUTO_RUN = {
    "list_files",
    "read_file",
    "memory_search",
    "memory_save",
}

SENSITIVE = {
    "terminal",
    "write_file",
    "delete_file",
    "send_notification",
    "clipboard_write",
}


def check(tool_name: str, arguments: dict) -> Decision:
    if tool_name in SAFE_TO_AUTO_RUN:
        return Decision(True)
    if tool_name in SENSITIVE:
        return Decision(True, True, "This operation can change device state or expose data.")
    return Decision(False, False, f"Unknown tool '{tool_name}' is not permitted.")
