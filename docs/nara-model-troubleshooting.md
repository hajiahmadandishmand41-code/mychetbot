# NaraRouter model troubleshooting

The backend sends OpenAI-compatible chat requests to:

- Base URL: `https://router.bynara.id/v1`
- Chat endpoint: `POST /chat/completions`
- Account-specific model list: `GET /models`

The application defaults to `laguna-s-2.1`, currently listed by NaraRouter in its public pricing catalog. This default is only a starting point: an authenticated `GET /v1/models` response is authoritative for aliases allowed by the particular API key and plan.

## Production model configuration

1. Make sure `NARA_API_KEY` is set only in Render's secret environment variables.
2. Call `GET https://router.bynara.id/v1/models` with the same key in the `Authorization: Bearer` header.
3. Copy an exact model `id` from the returned `data` list.
4. Set `DEFAULT_MODEL` to that exact ID.
5. Set `NARA_FALLBACK_MODELS` only to other IDs returned by the same endpoint, comma-separated.

Do not rely on stale aliases copied from examples or public catalogs. Do not invent `auto/*` aliases: the authenticated model list for the account is the source of truth.

## Common status codes

- `401`: missing or invalid API key.
- `402`: the request was rejected as payment-required by the gateway; inspect account balance, subscription and model billing in the NaraRouter dashboard.
- `403`: the API key is authenticated but the plan does not include that model, or the account is suspended.
- `404`: the requested model alias or endpoint does not exist.
- `429`: request rate, concurrency or per-model-tier daily quota has been exceeded.
- `503`: model service is temporarily unavailable.

Billing and account-wide rate-limit failures are not retried against alternative model names. Model fallback is only useful for aliases that the authenticated model list says the key can access.

Official documentation: https://router.bynara.id/docs
Current pricing/model catalog: https://router.bynara.id/pricing
