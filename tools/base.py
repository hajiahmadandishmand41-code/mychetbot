from __future__ import annotations

import inspect
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    args: dict[str, str]
    func: Callable[..., Any]
    dangerous: bool = False
    profiles: frozenset[str] = frozenset({"local", "device", "server"})
    unavailable_message: str = "This tool is unavailable in the current runtime."
    risk_level: str = "low"
    permission_scope: str = "read"
    runtime_requirements: tuple[str, ...] = field(default_factory=tuple)
    timeout_seconds: float = 10.0
    memory_limit_mb: int = 128
    process_limit: int = 8
    output_limit_chars: int = 4_000
    working_directory: str = "."
    allowed_environment: tuple[str, ...] = field(default_factory=tuple)
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
        if self.memory_limit_mb <= 0 or self.process_limit <= 0 or self.output_limit_chars <= 0:
            raise ValueError("resource limits must be positive")

    @property
    def input_schema(self) -> dict[str, str]:
        return dict(self.args)

    def available_in(self, profile: str) -> bool:
        return profile in self.profiles

    def run(self, args: dict) -> str:
        if not isinstance(args, dict):
            return "[arg-error] tool arguments must be an object"
        declared = set(self.args)
        unknown = set(args) - declared
        if unknown:
            return f"[arg-error] unsupported arguments: {sorted(unknown)}"
        try:
            signature = inspect.signature(self.func)
            required = {
                name
                for name, parameter in signature.parameters.items()
                if parameter.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
                and parameter.default is inspect.Parameter.empty
            }
        except (TypeError, ValueError):
            required = declared
        missing = required - set(args)
        if missing:
            return f"[arg-error] missing arguments: {sorted(missing)}"
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
            "memory_limit_mb": self.memory_limit_mb,
            "process_limit": self.process_limit,
            "output_limit_chars": self.output_limit_chars,
            "working_directory": self.working_directory,
            "allowed_environment": list(self.allowed_environment),
            "availability": sorted(self.profiles),
            "result_schema": self.result_schema,
            "auto_selectable": self.auto_selectable,
        }
