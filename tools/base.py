from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args: dict[str, str]
    func: Callable[..., Any]
    dangerous: bool = False
    profiles: frozenset[str] = frozenset({"local", "device"})
    unavailable_message: str = "This tool is unavailable in the current runtime."

    def available_in(self, profile: str) -> bool:
        return profile in self.profiles

    def run(self, args: dict) -> str:
        try:
            return str(self.func(**args))
        except TypeError as exc:
            return f"[arg-error] {exc}"
        except Exception as exc:  # noqa: BLE001
            return f"[error] {type(exc).__name__}: {exc}"
