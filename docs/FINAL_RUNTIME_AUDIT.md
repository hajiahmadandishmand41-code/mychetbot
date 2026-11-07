# Final Runtime Audit

This audit covers the current unified runtime path after the Nara, web-search, and Telegram fixes.

- Telegram and API enter the same `core.agent.Agent` facade.
- Topic research can auto-select `web_search`.
- Direct URLs can use `web_research` and URL comparisons use `web_compare`.
- Nara requests use a minimal `model` + `messages` payload for broad backend compatibility.
- The backend defaults to `laguna-s-2.1`; an explicit `DEFAULT_MODEL` overrides it, except the legacy `auto/bynara` alias is normalized to this concrete default. Operators should use only exact aliases returned by their authenticated `GET /v1/models` endpoint.
- Tool execution preserves session/profile policy through the canonical Agent implementation.
- Server execution stays disabled unless explicitly enabled, profiled, allowlisted, and session-authorized.
- Web content is untrusted data and SSRF/private destinations are blocked.
- Secrets are redacted before user-facing output and relevant memory/tool-result paths.
