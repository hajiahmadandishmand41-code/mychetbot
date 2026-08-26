from __future__ import annotations

import json

from tools import shell_tool, files_tool, network_tool, wifi_tool, termux_tool, http_tool, notes_tool
from tools.base import Tool

SERVER_SAFE = frozenset({"server", "local", "device"})
LOCAL_ONLY = frozenset({"local", "device"})
DEVICE_ONLY = frozenset({"device"})

TOOLS: dict[str, Tool] = {}


def register(t: Tool) -> None:
    TOOLS[t.name] = t


register(Tool("shell", "اجرای دستور شل (whitelist شده)", {"command": "str"}, shell_tool.shell, dangerous=True, profiles=LOCAL_ONLY))
register(Tool("list_dir", "لیست فایل‌های یک پوشه", {"path": "str"}, files_tool.list_dir, profiles=LOCAL_ONLY))
register(Tool("read_file", "خواندن فایل متنی", {"path": "str"}, files_tool.read_file, profiles=LOCAL_ONLY))
register(Tool("write_file", "نوشتن فایل", {"path": "str", "content": "str"}, files_tool.write_file, dangerous=True, profiles=LOCAL_ONLY))
register(Tool("ping", "پینگ یک هاست", {"host": "str"}, network_tool.ping, profiles=LOCAL_ONLY))
register(Tool("dns_lookup", "تبدیل دامنه به IP", {"host": "str"}, network_tool.dns_lookup, profiles=LOCAL_ONLY))
register(Tool("port_check", "بررسی باز بودن پورت", {"host": "str", "port": "int"}, network_tool.port_check, profiles=LOCAL_ONLY))
register(Tool("local_ip", "IP محلی دستگاه", {}, network_tool.local_ip, profiles=LOCAL_ONLY))
register(Tool("wifi_capabilities", "تشخیص قابلیت‌ها و محدودیت‌های قانونی Wi-Fi Audit", {}, wifi_tool.capability_detection, profiles=DEVICE_ONLY))
register(Tool("wifi_info", "اطلاعات اتصال Wi-Fi فعلی", {}, wifi_tool.wifi_info, profiles=DEVICE_ONLY))
register(Tool("wifi_scan", "اسکن غیرفعال شبکه‌های Wi-Fi اطراف با اطلاعات امنیتی", {}, wifi_tool.wifi_scan, profiles=DEVICE_ONLY))
register(Tool("wifi_diagnostics", "تشخیص اتصال، مسیر، DNS و دسترسی اینترنت Wi-Fi", {}, wifi_tool.network_diagnostics, profiles=DEVICE_ONLY))
register(Tool("wifi_security_report", "گزارش امنیتی passive برای شبکه Wi-Fi فعلی", {}, wifi_tool.security_report, profiles=DEVICE_ONLY))
register(Tool("battery", "وضعیت باتری", {}, termux_tool.battery, profiles=DEVICE_ONLY))
register(Tool("notify", "ارسال نوتیفیکیشن اندروید", {"title": "str", "content": "str"}, termux_tool.notify, profiles=DEVICE_ONLY))
register(Tool("toast", "نمایش toast", {"text": "str"}, termux_tool.toast, profiles=DEVICE_ONLY))
register(Tool("speak", "تبدیل متن به گفتار", {"text": "str"}, termux_tool.speak, profiles=DEVICE_ONLY))
register(Tool("clipboard_get", "خواندن کلیپ‌بورد", {}, termux_tool.clipboard_get, profiles=DEVICE_ONLY))
register(Tool("clipboard_set", "نوشتن در کلیپ‌بورد", {"text": "str"}, termux_tool.clipboard_set, profiles=DEVICE_ONLY))
register(Tool("location", "موقعیت مکانی", {}, termux_tool.location, profiles=DEVICE_ONLY))
register(Tool("http_get", "دریافت محتوای یک URL", {"url": "str"}, http_tool.http_get, profiles=LOCAL_ONLY))
register(Tool("remember", "ذخیره یک حقیقت درباره کاربر", {"key": "str", "value": "str"}, notes_tool.remember, profiles=SERVER_SAFE))
register(Tool("recall", "بازیابی حقیقت ذخیره‌شده", {"key": "str"}, notes_tool.recall, profiles=SERVER_SAFE))
register(Tool("list_facts", "لیست همه حقایق", {}, notes_tool.list_facts, profiles=SERVER_SAFE))


def tool_specs(profile: str = "local") -> list[dict]:
    return [
        {"name": t.name, "description": t.description, "args": t.args}
        for t in TOOLS.values()
        if t.available_in(profile)
    ]


def run_tool(name: str, args: dict, profile: str = "local") -> str:
    tool = TOOLS.get(name)
    if not tool:
        return json.dumps({"error": "unknown_tool", "message": f"Unknown tool: {name}"}, ensure_ascii=False)
    if not tool.available_in(profile):
        return json.dumps({"error": "capability_unavailable", "message": tool.unavailable_message if tool.unavailable_message != "This tool is unavailable in the current runtime." else f"Tool '{name}' requires a different runtime capability profile.", "tool": name, "profile": profile}, ensure_ascii=False)
    return tool.run(args)
