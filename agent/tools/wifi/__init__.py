"""Wi-Fi and local-network tools for MyChatBot.

These tools are intended for the user's own device/network. Read-only network
information is SAFE; active scanning is CONFIRM and must be authorized.
"""
from .manager import build_wifi_tools

__all__ = ["build_wifi_tools"]
