"""Central decision loop: user -> model -> tool -> permission -> result -> model."""
import json
from agent.ai.providers import get_provider
from agent.memory.store import MemoryStore
from agent.tools.registry import ToolRegistry

SYSTEM = """You are MyChatBot, a personal Android + Termux assistant.
Use tools when needed. Never claim an operation happened unless its tool result confirms it.
Sensitive operations must be presented for user confirmation before execution.
Keep responses concise and explain important side effects."""


class Agent:
    def __init__(self, registry: ToolRegistry, memory: MemoryStore):
        self.registry = registry
        self.memory = memory

    def run(self, user_text: str, provider_name: str | None = None, model: str | None = None, history: list[dict] | None = None):
        memories = self.memory.search(user_text, 5)
        context = "\n".join(f"- {m['content']}" for m in memories)
        messages = [{"role": "system", "content": SYSTEM + (f"\nRelevant memory:\n{context}" if context else "") }]
        messages.extend((history or [])[-20:])
        messages.append({"role": "user", "content": user_text})
        provider = get_provider(provider_name)
        model = model or __import__("os").getenv("AI_MODEL", "gpt-5.6-luna")

        for _ in range(8):
            response = provider.chat(messages, model, self.registry.definitions())
            message = response.get("choices", [{}])[0].get("message", {})
            tool_calls = message.get("tool_calls") or []
            if not tool_calls:
                answer = message.get("content", "")
                self.memory.save("conversation", f"User: {user_text}\nAssistant: {answer}")
                return {"ok": True, "content": answer, "pending": None}

            messages.append(message)
            pending = []
            for call in tool_calls:
                name = call["function"]["name"]
                args = json.loads(call["function"].get("arguments", "{}"))
                result = self.registry.execute(name, args, confirmed=False)
                if result.get("confirmation_required"):
                    pending.append({"name": name, "arguments": args, "reason": result["reason"]})
                    continue
                messages.append({"role": "tool", "tool_call_id": call.get("id", name), "content": json.dumps(result, ensure_ascii=False)})
            if pending:
                return {"ok": True, "content": "This action needs your confirmation before I execute it.", "pending": pending}
        return {"ok": False, "content": "Agent stopped after reaching the tool-call limit.", "pending": None}
