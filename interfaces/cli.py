from __future__ import annotations
import asyncio, sys
from rich.console import Console
from rich.markdown import Markdown
from core.agent import Agent
from core.config import config
from providers.registry import list_providers

console = Console()

BANNER = '''[bold cyan]MyChatBot[/] — Personal AI Assistant (Termux)
providers: {p} | default: {d} | shell: {s}
دستورات: /exit  /clear  /facts  /tools  /provider <name>'''

async def main() -> None:
    agent = Agent(session="cli")
    console.print(BANNER.format(p=", ".join(list_providers()), d=config.default_provider,
                                s="on" if config.allow_shell else "off"))
    while True:
        try:
            user = console.input("[bold green]شما ›[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user:
            continue
        if user == "/exit":
            break
        if user == "/clear":
            agent.memory.clear("cli"); console.print("حافظه پاک شد."); continue
        if user == "/facts":
            console.print(agent.memory.all_facts()); continue
        if user == "/tools":
            from tools.registry import tool_specs
            for s in tool_specs():
                console.print(f"- [cyan]{s['name']}[/]: {s['description']}")
            continue
        if user.startswith("/provider "):
            agent.router.preferred = user.split(maxsplit=1)[1]
            console.print(f"provider -> {agent.router.preferred}"); continue
        try:
            answer = await agent.ask(user)
            console.print(Markdown(answer))
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]خطا:[/] {exc}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        sys.exit(0)
