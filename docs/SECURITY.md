# امنیت

- **کلیدها**: فقط از `.env` خوانده می‌شوند؛ `.env` در `.gitignore` است. کلید محلی با Fernet رمز می‌شود (`~/.mychatbot/.master.key`, chmod 600).
- **Shell**: به‌صورت پیش‌فرض غیرفعال (`ALLOW_SHELL=false`). فعال‌سازی + whitelist + regex ضد دستورات مخرب (`rm -rf /`, `mkfs`, fork bomb, `dd if=`).
- **Filesystem**: ابزار فایل به `$HOME` sandbox شده؛ path traversal مسدود است.
- **HTTP tool**: مسدودسازی آدرس‌های metadata (SSRF).
- **API**: توکن Bearer با مقایسه constant-time؛ پیش‌فرض bind روی `127.0.0.1`.
- **Logging**: فیلتر redaction روی هر خطی که شبیه کلید/توکن باشد.
- **حریم خصوصی**: با provider `ollama` هیچ داده‌ای از دستگاه خارج نمی‌شود.

## توصیه‌ها
- `API_TOKEN` را حتماً عوض کنید.
- در حالت اشتراک شبکه، از SSH tunnel به‌جای bind روی `0.0.0.0` استفاده کنید.
