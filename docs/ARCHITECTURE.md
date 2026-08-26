# معماری Unified MyChatBot

```text
                    ┌───────────────┐
                    │ User          │
                    └──────┬────────┘
                           │ natural language only
                 ┌─────────▼─────────┐
                 │ Telegram / API    │  Interfaces only
                 └─────────┬─────────┘
                           │
                 ┌─────────▼─────────┐
                 │ Unified Agent     │  core/agent.py
                 │ intent + context  │
                 │ memory + planning │
                 └──────┬─────┬──────┘
                        │     │
                ┌───────▼┐   └─────────────┐
                │Memory  │                 │
                │SQLite  │                 │
                └────────┘          ┌───────▼────────┐
                                    │ Internal Tools │
                                    │ registry/base  │
                                    └───────┬────────┘
                                            │ structured data
                                    ┌───────▼────────┐
                                    │ Interpretation  │
                                    │ + final reply  │
                                    └───────┬────────┘
                                            │
                                      User sees reply

Unified Agent ──> Router ──> NaraRouter (provider)
                         model = DEFAULT_MODEL (environment only)
```

## Architectural rules

1. Telegram and API are transport interfaces only; they never implement business intent or tool semantics.
2. The user interacts with one conversational surface. Tools are internal capabilities and never address the user directly.
3. Tool selection is allow-listed, profile-aware, metadata-driven and limited to `auto_selectable` read-only tools.
4. Dangerous/write tools remain registered for explicit backend use but cannot be executed through the automatic conversational tool path.
5. Tool output is untrusted data. It is never treated as an instruction.
6. API logical sessions are bound to the authenticated API principal before reaching persistent memory.
7. Memory is persistent, session-isolated, relevance-ranked and bounded by configurable message/fact limits.
8. Provider/model configuration is environment-driven. Provider identity is not exposed as the bot's conversational identity.
9. Android/Termux capabilities remain internal runtime capabilities. Server profile does not expose device-only tools.
10. Health is liveness; readiness verifies required runtime configuration.

## Runtime profiles

- `local`: filesystem/network capabilities available according to the registered profile; device-only tools remain unavailable unless the runtime selects `device`.
- `device`: Android/Termux capabilities such as Wi-Fi and battery can be available.
- `server`: no Android/Termux/local capability exposure; only server-safe tools such as memory operations are available.
