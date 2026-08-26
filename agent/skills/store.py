"""Simple persistent Markdown skill store for reusable user-approved workflows."""
from pathlib import Path
import re


class SkillStore:
    def __init__(self, root: str = "runtime/skills"):
        self.root = Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, name: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_-]+", "-", name).strip("-")
        if not safe:
            raise ValueError("invalid skill name")
        return safe[:80]

    def list(self) -> list[str]:
        return sorted(p.stem for p in self.root.glob("*.md"))

    def read(self, name: str) -> str:
        path = self.root / f"{self._safe_name(name)}.md"
        return path.read_text(encoding="utf-8")

    def save(self, name: str, content: str) -> str:
        path = self.root / f"{self._safe_name(name)}.md"
        if not content.strip():
            raise ValueError("skill content is required")
        path.write_text(content.strip() + "\n", encoding="utf-8")
        return str(path)
