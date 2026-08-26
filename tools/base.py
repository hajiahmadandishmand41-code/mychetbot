from __future__ import annotations

from dataclasses import dataclass, field
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
    risk_level: str = "low"
    permission_scope: str = "read"
    runtime_requirements: tuple[str, ...] = field(default_factory=tuple)
    timeout_seconds: float = 10.0
    result_schema: str = "string"
    auto_selectable: bool = True

    def __post_init__(self) -> None:
        valid_risk = {"low", "medium", "high", "critical"}
        valid_scope = {"read", "write", "external"}
        if self.risk_level not in valid_risk:
            raise ValueError(f"invalid risk_level: {self.risk_level}")
        if self.permission_scope not in valid_scope:
            raise ValueError(f"invalid permission_scope: {self.permission_scope}")
        if self.timeout_seconds <= 0 or self.timeout_seconds > 120:
            raise ValueError("timeout_seconds must be between 0 and 120")

    @property
    def input_schema(self) -> dict[str, str]:
        return dict(self.args)

    def available_in(self, profile: str) -> bool:
        return profile in self.profiles

    def run(self, args: dict) -> str:
        if not isinstance(args, dict):
            return "[arg-error] tool arguments must be an object"
        required = set(self.args)
        unknown = set(args) - required
        if unknown:
            return f"[arg-error] unsupported arguments: {sorted(unknown)}"
        try:
            return str(self.func(**args))
        except TypeError as exc:
            return f"[arg-error] {exc}"
        except Exception as exc:  # noqa: BLE001
            return f"[error] {type(exc).__name__}: {exc}"

    def metadata(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
            "risk_level": self.risk_level,
            "permission_scope": self.permission_scope,
            "runtime_requirements": list(self.runtime_requirements),
            "timeout": self.timeout_seconds,
            "availability": self.profiles,
            "result_schema": self.result_schema,
            "auto_selectable": self.auto_selectable,
        }
