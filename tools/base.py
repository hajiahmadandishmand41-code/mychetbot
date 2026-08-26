from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Any

@dataclass
class Tool:
    name: str
    description: str
    args: dict[str, str]
    func: Callable[..., Any]
    dangerous: bool = False

    def run(self, args: dict) -> str:
        try:
            return str(self.func(**args))
        except TypeError as exc:
            return f"[arg-error] {exc}"
        except Exception as exc:  # noqa: BLE001
            return f"[error] {type(exc).__name__}: {exc}"
