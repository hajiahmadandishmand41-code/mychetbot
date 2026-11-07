# NaraRouter model troubleshooting

The Render/FastAPI backend sends OpenAI-compatible chat requests to:

`https://router.bynara.id/v1/chat/completions`

The base URL is `https://router.bynara.id/v1`. The chat path is `/chat/completions`.

## Model selection

The application selects models in this order:

1. `DEFAULT_MODEL` (defaults to `auto/bynara`).
2. `NARA_FALLBACK_MODELS` when the selected model is rejected as unavailable or not entitled.

The code's fallback defaults are refreshed against NaraRouter's public Free-tier catalog:
- `agnes-2.5-flash`
- `laguna-s-2.1`
- `nemotron-3.5-lightning-free`

The authenticated `GET /v1/models` response is authoritative for one API key and account plan. Use the aliases returned by that endpoint; the public catalog alone does not guarantee that a particular key can use every model.

## Error meanings

- `401`: the API key is missing or invalid.
- `402`: payment, available-credit, or model billing requirement. Do not retry the same failure across several models as though it were a transport issue.
- `403`: the plan does not grant access to the selected model, or the account is restricted.
- `404`: the endpoint or model alias was not found.
- `429`: request, concurrency, or model-tier quota was reached.
- `5xx`: temporary upstream/server failure.

Billing failures and account-wide rate limits are not retried against alternative model names. Only model/request rejection and temporary upstream server failures use the configured fallback list.

Official API documentation: https://router.bynara.id/docs
Official plans: https://router.bynara.id/pricing
