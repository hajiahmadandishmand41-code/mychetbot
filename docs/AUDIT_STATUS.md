# Audit Status

Latest audited base head: `d3e776a92c250f532c5d2342fa2c6d7f0e591c09`
Latest fix candidate: PR #14 (`fix/runtime-routing-and-deploy`)

## Unified Agent routing
- Telegram and API continue to enter the same `core.agent.Agent` facade.
- The Agent preserves one session per conversation and one Tool Registry/policy path.
- Topic questions can select `web_search`; direct URLs can select `web_research`; URL comparisons use `web_compare`.
- Tool execution preserves the chat session when passing through the compatibility facade, including server-side session/allowlist checks.

## Web routing fixes in PR #14
- `/api/chat` now reuses the canonical Web Nara implementation instead of maintaining a second provider implementation.
- Shared same-origin and rate-limit guards are used by the chat route.
- Backend proxy routing rejects origin changes and correctly accepts `/history/...` and `/memory/...` paths.
- Node 22 is used by Web CI to match the pinned production runtime.
- Branded `404` and route-error recovery pages were added without changing the existing chat surface.

## Identity
- Creator: حاجی احمد صالحی
- Team: تیم ربات‌های سازنده @فکر کن
- Key project areas: unified conversational AI, Web Research, Memory, Telegram/API, Android/Termux, legal Wi-Fi diagnostics, Server/Render diagnostics, and security.

## Security boundaries
- Web content remains untrusted DATA.
- SSRF/private/special destinations are blocked by Web Research.
- Secrets are redacted before tool results/memory/answers where applicable.
- Server execution remains disabled unless explicitly enabled, profiled, allowlisted, and session-authorized.
- Arbitrary shell execution is not auto-selectable.

## CI verification target
Acceptance remains dependent on the actual GitHub Actions/Vercel verification for PR #14. The latest backend CI matrix on the audited base head is green; the previous production deploy failure was caused by missing VPS deployment secrets after successful image build, health-check, and GHCR publication.
