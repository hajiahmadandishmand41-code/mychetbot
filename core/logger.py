from __future__ import annotations
import logging, os, sys
from logging.handlers import RotatingFileHandler
from core.config import config

_SECRET_HINTS = ("key", "token", "secret", "password")

class RedactFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        msg = str(record.getMessage())
        for hint in _SECRET_HINTS:
            if hint in msg.lower():
                record.msg = "[redacted-possible-secret] " + msg[:40]
                record.args = ()
                break
        return True

def get_logger(name: str = "mychatbot") -> logging.Logger:
    log = logging.getLogger(name)
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s")
    sh = logging.StreamHandler(sys.stdout); sh.setFormatter(fmt)
    fh = RotatingFileHandler(os.path.join(config.data_dir, "mychatbot.log"),
                             maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    for h in (sh, fh):
        h.addFilter(RedactFilter()); log.addHandler(h)
    return log
