from __future__ import annotations

import json
import logging
import time

from tools import (
    files_tool,
    http_tool,
    network_tool,
    notes_tool,
    server_execution,
    shell_tool,
    termux_tool,
    web_research,
    web_search,
    wifi_tool,
)
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
register(Tool("web_search", "جستجوی عمومی وب و واکشی صفحات مرتبط با سؤال کاربر", {"query": "str"}, web_search.search_and_research, profiles=frozenset({"local", "server"}), risk_level="low", permission_scope="external", runtime_requirements=("network",), timeout_seconds=60, memory_limit_mb=256, process_limit=8, output_limit_chars=160000, result_schema="json:web_search", auto_selectable=True))
register(Tool("web_research", "تحقیق و استخراج ساختاریافته از یک صفحه عمومی وب", {"url": "str"}, web_research.research_page, profiles=frozenset({"local", "server"}), risk_level="low", permission_scope="external", runtime_requirements=("network",), timeout_seconds=30, memory_limit_mb=128, process_limit=4, output_limit_chars=120000, result_schema="json:web_research", auto_selectable=True))
register(Tool("web_compare", "دریافت و مقایسه دو تا پنج صفحه عمومی وب", {"urls_json": "str"}, web_research.compare_pages, profiles=frozenset({"local", "server"}), risk_level="low", permission_scope="external", runtime_requirements=("network",), timeout_seconds=60, memory_limit_mb=256, process_limit=6, output_limit_chars=200000, result_schema="json:web_compare", auto_selectable=True))
register(Tool("server_diagnostics", "تشخیص read-only در runtime سرور Render", {"operation": "str", "path": "str", "script": "str", "timeout": "int"}, server_execution.execute, profiles=frozenset({"server"}), risk_level="low", permission_scope="read", runtime_requirements=("server_runtime",), timeout_seconds=30, memory_limit_mb=256, process_limit=16, output_limit_chars=12000, working_directory="project_root", allowed_environment=("PATH", "HOME", "PYTHONPATH"), result_schema="json:server_execution", auto_selectable=True))
register(Tool("server_execute", "اجرای script داخلی و از پیش allowlist شده در Render runtime", {"operation": "str", "path": "str", "script": "str", "timeout": "int"}, server_execution.execute, profiles=frozenset({"server"}), risk_level="high", permission_scope="write", runtime_requirements=("server_runtime",), timeout_seconds=30, memory_limit_mb=256, process_limit=16, output_limit_chars=12000, working_directory="project_root", allowed_environment=("PATH", "HOME", "PYTHONPATH"), result_schema="json:server_execution", auto_selectable=False))
register(Tool("remember", "ذخیره یک حقیقت درباره کاربر", {"key": "str", "value": "str"}, notes_tool.remember, profiles=SERVER_SAFE, permission_scope="write", auto_selectable=False))
register(Tool("recall", "بازیابی حقیقت ذخیره‌شده", {"key": "str"}, notes_tool.recall, profiles=SERVER_SAFE, auto_selectable=False))
register(Tool("list_facts", "لیست همه حقایق", {}, notes_tool.list_facts, profiles=SERVER_SAFE, auto_selectable=False))


def tool_specs(profile: str = "local") -> list[dict]:
    return [t.metadata() for t in TOOLS.values() if t.available_in(profile)]


def run_tool(name: str, args: dict, profile: str = "local", session: str = "default") -> str:
    request_logger = logging.getLogger("mychatbot.tools")
    tool = TOOLS.get(name)
    if not tool:
        return json.dumps({"status": "error", "error": "unknown_tool", "message": f"Unknown tool: {name}"}, ensure_ascii=False)
    if not tool.available_in(profile):
        return json.dumps({"status": "error", "error": "capability_unavailable", "tool": name, "profile": profile}, ensure_ascii=False)
    if tool.dangerous:
        return json.dumps({"status": "denied", "error": "permission_required", "message": "این ابزار برای اجرای خودکار مجاز نیست و تأیید صریح لازم دارد.", "tool": name}, ensure_ascii=False)
    if name == "server_execute":
        from core.config import config

        if not config.server_execution_enabled or profile != "server" or session not in config.server_exec_allowed_sessions:
            return json.dumps({"status": "denied", "error": "unauthorized", "message": "مجوز اجرای script داخلی برای این session فعال نیست."}, ensure_ascii=False)
        if "server_execute" not in config.server_exec_allowlist:
            return json.dumps({"status": "denied", "error": "allowlist", "message": "server_execute در allowlist فعال نیست."}, ensure_ascii=False)
    request_id = f"tool-{time.time_ns()}"
    started = time.monotonic()
    try:
        result = tool.run(args)
        duration_ms = int((time.monotonic() - started) * 1000)
        status = "success"
        try:
            parsed = json.loads(result)
            status = str(parsed.get("status", status)) if isinstance(parsed, dict) else status
        except json.JSONDecodeError:
            if result.startswith(("[error]", "[blocked]", "[timeout]", "[arg-error]")):
                status = "error"
        request_logger.info("tool=%s request_id=%s session=%s status=%s duration_ms=%s", name, request_id, session[:32], status, duration_ms)
        return result
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.monotonic() - started) * 1000)
        request_logger.error("tool=%s request_id=%s session=%s status=error error_type=%s duration_ms=%s", name, request_id, session[:32], type(exc).__name__, duration_ms)
        return json.dumps({"status": "error", "error": type(exc).__name__}, ensure_ascii=False)
