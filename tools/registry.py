from __future__ import annotations
from tools.base import Tool
from tools import shell_tool, files_tool, network_tool, wifi_tool, termux_tool, http_tool, notes_tool

TOOLS: dict[str, Tool] = {}

def register(t: Tool) -> None:
    TOOLS[t.name] = t

register(Tool("shell", "اجرای دستور شل (whitelist شده)", {"command": "str"}, shell_tool.shell, dangerous=True))
register(Tool("list_dir", "لیست فایل‌های یک پوشه", {"path": "str"}, files_tool.list_dir))
register(Tool("read_file", "خواندن فایل متنی", {"path": "str"}, files_tool.read_file))
register(Tool("write_file", "نوشتن فایل", {"path": "str", "content": "str"}, files_tool.write_file, dangerous=True))
register(Tool("ping", "پینگ یک هاست", {"host": "str"}, network_tool.ping))
register(Tool("dns_lookup", "تبدیل دامنه به IP", {"host": "str"}, network_tool.dns_lookup))
register(Tool("port_check", "بررسی باز بودن پورت", {"host": "str", "port": "int"}, network_tool.port_check))
register(Tool("local_ip", "IP محلی دستگاه", {}, network_tool.local_ip))
register(Tool("wifi_info", "اطلاعات اتصال Wi-Fi فعلی", {}, wifi_tool.wifi_info))
register(Tool("wifi_scan", "اسکن شبکه‌های Wi-Fi اطراف", {}, wifi_tool.wifi_scan))
register(Tool("battery", "وضعیت باتری", {}, termux_tool.battery))
register(Tool("notify", "ارسال نوتیفیکیشن اندروید", {"title": "str", "content": "str"}, termux_tool.notify))
register(Tool("toast", "نمایش toast", {"text": "str"}, termux_tool.toast))
register(Tool("speak", "تبدیل متن به گفتار", {"text": "str"}, termux_tool.speak))
register(Tool("clipboard_get", "خواندن کلیپ‌بورد", {}, termux_tool.clipboard_get))
register(Tool("clipboard_set", "نوشتن در کلیپ‌بورد", {"text": "str"}, termux_tool.clipboard_set))
register(Tool("location", "موقعیت مکانی", {}, termux_tool.location))
register(Tool("http_get", "دریافت محتوای یک URL", {"url": "str"}, http_tool.http_get))
register(Tool("remember", "ذخیره یک حقیقت درباره کاربر", {"key": "str", "value": "str"}, notes_tool.remember))
register(Tool("recall", "بازیابی حقیقت ذخیره‌شده", {"key": "str"}, notes_tool.recall))
register(Tool("list_facts", "لیست همه حقایق", {}, notes_tool.list_facts))

def tool_specs() -> list[dict]:
    return [{"name": t.name, "description": t.description, "args": t.args} for t in TOOLS.values()]

def run_tool(name: str, args: dict) -> str:
    tool = TOOLS.get(name)
    if not tool:
        return f"[unknown-tool] {name}"
    return tool.run(args)
