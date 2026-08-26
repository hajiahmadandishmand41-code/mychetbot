# Final Runtime Audit

This audit covers the current unified runtime path after the Nara, web-search, and Telegram fixes.

- Telegram and API enter the same `core.agent.Agent` facade.
- Topic research can auto-select `web_search`.
- Direct URLs can use `web_research` and URL comparisons use `web_compare`.
- Nara requests use a minimal `model` + `messages` payload for broad backend compatibility.
- The default Nara model is `agnes-2.0-flash` when `DEFAULT_MODEL` is omitted; operators may override it.
- Tool execution preserves session/profile policy through the canonical Agent implementation.
- Server execution stays disabled unless explicitly enabled, profiled, allowlisted, and session-authorized.
- Web content is untrusted data and SSRF/private destinations are blocked.
- Secrets are redacted before user-facing output and relevant memory/tool-result paths.
