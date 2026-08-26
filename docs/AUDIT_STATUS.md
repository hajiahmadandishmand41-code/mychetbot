# Audit Status

Latest verified development head: `a4663798c23c03c16e513b434ddda6b3b662f174`

## Unified Agent routing
- Telegram and API continue to enter the same `core.agent.Agent` facade.
- The Agent preserves one session per conversation and one Tool Registry/policy path.
- Topic questions can select `web_search`; direct URLs can select `web_research`; URL comparisons use `web_compare`.
- Tool execution preserves the chat session when passing through the compatibility facade, including server-side session/allowlist checks.

## Identity
- Creator: حاجی احمد صالحی
- Team: افکاران
- Key project areas: unified conversational AI, Web Research, Memory, Telegram/API, Android/Termux, legal Wi-Fi diagnostics, Server/Render diagnostics, and security.

## Security boundaries
- Web content remains untrusted DATA.
- SSRF/private/special destinations are blocked by Web Research.
- Secrets are redacted before tool results/memory/answers where applicable.
- Server execution remains disabled unless explicitly enabled, profiled, allowlisted, and session-authorized.
- Arbitrary shell execution is not auto-selectable.

## CI verification target
This PR exists only to run the complete CI matrix over the latest `main` implementation, including the new Telegram/session and creator/web-routing regression tests. Acceptance remains dependent on the actual GitHub Actions results for this PR.
