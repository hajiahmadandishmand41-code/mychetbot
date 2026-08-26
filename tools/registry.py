from __future__ import annotations

import json

from tools import files_tool, http_tool, network_tool, notes_tool, shell_tool, termux_tool, wifi_tool
from tools.base import Tool

SERVER_SAFE = frozenset({"server", "local", "device"})
LOCAL_ONLY = frozenset({"local", "device"})
DEVICE_ONLY = frozenset({"device"})

TOOLS: dict[str, Tool] = {}


def register(t: Tool) -> None:
    TOOLS[t.name] = t


register(Tool("shell", "اجرای دستور شل (whitelist شده)", {"command": "str"}, shell_tool.shell, dangerous=True, profiles=LOCAL_ONLY, risk_level="high", permission_scope="write", auto_selectable=False))
register(Tool("list_dir", "لیست فایل‌های یک پوشه", {"path": "str"}, files_tool.list_dir, profiles=LOCAL_ONLY, runtime_requirements=("filesystem",)))
register(Tool("read_file", "خواندن فایل متنی", {"path": "str"}, files_tool.read_file, profiles=LOCAL_ONLY, runtime_requirements=("filesystem",)))
register(Tool("write_file", "نوشتن فایل", {"path": "str", "content": "str"}, files_tool.write_file, dangerous=True, profiles=LOCAL_ONLY, risk_level="high", permission_scope="write", runtime_requirements=("filesystem",), auto_selectable=False))
register(Tool("ping", "پینگ یک هاست", {"host": "str"}, network_tool.ping, profiles=LOCAL_ONLY, runtime_requirements=("network",)))
register(Tool("dns_lookup", "تبدیل دامنه به IP", {"host": "str"}, network_tool.dns_lookup, profiles=LOCAL_ONLY, runtime_requirements=("network",)))
register(Tool("port_check", "بررسی باز بودن پورت", {"host": "str", "port": "int"}, network_tool.port_check, profiles=LOCAL_ONLY, runtime_requirements=("network",)))
register(Tool("local_ip", "IP محلی دستگاه", {}, network_tool.local_ip, profiles=LOCAL_ONLY, runtime_requirements=("network",)))
register(Tool("wifi_capabilities", "تشخیص قابلیت‌ها و محدودیت‌های قانونی Wi-Fi Audit", {}, wifi_tool.capability_detection, profiles=DEVICE_ONLY, runtime_requirements=("android_wifi",)))
register(Tool("wifi_info", "اطلاعات اتصال Wi-Fi فعلی", {}, wifi_tool.wifi_info, profiles=DEVICE_ONLY, runtime_requirements=("android_wifi",)))
register(Tool("wifi_scan", "اسکن غیرفعال شبکه‌های Wi-Fi اطراف با اطلاعات امنیتی", {}, wifi_tool.wifi_scan, profiles=DEVICE_ONLY, runtime_requirements=("android_wifi",)))
register(Tool("wifi_diagnostics", "تشخیص اتصال، مسیر، DNS و دسترسی اینترنت Wi-Fi", {}, wifi_tool.network_diagnostics, profiles=DEVICE_ONLY, runtime_requirements=("android_wifi", "network")))
register(Tool("wifi_security_report", "گزارش امنیتی passive برای شبکه Wi-Fi فعلی", {}, wifi_tool.security_report, profiles=DEVICE_ONLY, runtime_requirements=("android_wifi",)))
register(Tool("battery", "وضعیت باتری", {}, termux_tool.battery, profiles=DEVICE_ONLY, runtime_requirements=("termux_api",)))
register(Tool("notify", "ارسال نوتیفیکیشن اندروید", {"title": "str", "content": "str"}, termux_tool.notify, profiles=DEVICE_ONLY, permission_scope="write", auto_selectable=False))
register(Tool("toast", "نمایش toast", {"text": "str"}, termux_tool.toast, profiles=DEVICE_ONLY, permission_scope="write", auto_selectable=False))
register(Tool("speak", "تبدیل متن به گفتار", {"text": "str"}, termux_tool.speak, profiles=DEVICE_ONLY, permission_scope="write", auto_selectable=False))
register(Tool("clipboard_get", "خواندن کلیپ‌بورد", {}, termux_tool.clipboard_get, profiles=DEVICE_ONLY, runtime_requirements=("termux_api",)))
register(Tool("clipboard_set", "نوشتن در کلیپ‌بورد", {"text": "str"}, termux_tool.clipboard_set, profiles=DEVICE_ONLY, permission_scope="write", auto_selectable=False))
register(Tool("location", "موقعیت مکانی", {}, termux_tool.location, profiles=DEVICE_ONLY, permission_scope="external", auto_selectable=False))
register(Tool("http_get", "دریافت محتوای یک URL عمومی", {"url": "str"}, http_tool.http_get, profiles=LOCAL_ONLY, runtime_requirements=("network",)))
register(Tool("remember", "ذخیره یک حقیقت درباره کاربر", {"key": "str", "value": "str"}, notes_tool.remember, profiles=SERVER_SAFE, permission_scope="write", auto_selectable=False))
register(Tool("recall", "بازیابی حقیقت ذخیره‌شده", {"key": "str"}, notes_tool.recall, profiles=SERVER_SAFE, auto_selectable=False))
register(Tool("list_facts", "لیست همه حقایق", {}, notes_tool.list_facts, profiles=SERVER_SAFE, auto_selectable=False))


def tool_specs(profile: str = "local") -> list[dict]:
    return [t.metadata() for t in TOOLS.values() if t.available_in(profile)]


def run_tool(name: str, args: dict, profile: str = "local") -> str:
    tool = TOOLS.get(name)
    if not tool:
        return json.dumps({"error": "unknown_tool", "message": f"Unknown tool: {name}"}, ensure_ascii=False)
    if not tool.available_in(profile):
        return json.dumps(
            {
                "error": "capability_unavailable",
                "message": tool.unavailable_message
                if tool.unavailable_message != "This tool is unavailable in the current runtime."
                else f"Tool '{name}' requires a different runtime capability profile.",
                "tool": name,
                "profile": profile,
            },
            ensure_ascii=False,
        )
    if tool.dangerous:
        return json.dumps(
            {"error": "permission_required", "message": "این ابزار برای اجرای خودکار مجاز نیست و تأیید صریح لازم دارد.", "tool": name},
            ensure_ascii=False,
        )
    return tool.run(args)
