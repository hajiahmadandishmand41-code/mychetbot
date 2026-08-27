# NaraRouter model troubleshooting

The Web Chat sends OpenAI-compatible requests to `https://router.bynara.id/v1/chat/completions`.

Model selection order:

1. `NARA_MODEL`
2. `DEFAULT_MODEL` (legacy compatibility)
3. `auto/bynara`

If Nara reports that the requested model does not exist, the Web runtime retries once with `NARA_FALLBACK_MODEL` (default: `agnes-2.0-flash`). Other Nara errors are not retried as model errors and are returned with their HTTP status/type/message for diagnosis.

Nara's public site currently documents `auto/bynara` as a valid routing alias and lists `Agnes 2.0 Flash` in the Free plan. Model availability and aliases can change over time, so production configuration should use a currently supported model for the account/plan.
