# MyChatBot

MyChatBot is a modular Python assistant that supports two intentionally separated runtimes:

1. **Android + Termux** for device capabilities such as Wi-Fi, battery, notifications, clipboard and location.
2. **Docker + Linux VPS** for the FastAPI service, AI providers, persistent memory and HTTPS deployment.

The same repository supports both without making the VPS container depend on Android, Termux, phone root or Android permissions.

## Architecture

```text
GitHub
  |
  | push main
  v
GitHub Actions
  |
  +--> CI: Python 3.10 / 3.13 / 3.14 + pytest
  |
  +--> Docker build + /health verification
          |
          +--> GHCR immutable image: <commit-sha>
                    |
                    | SSH deploy
                    v
             Linux VPS / Docker Compose
                    |
                    +--> mychatbot API (internal :8765)
                    +--> persistent ./data bind mount
                    +--> Caddy (80/443, automatic HTTPS)
                    +--> health-gated rollback

Android / Termux
  |
  +--> CLI / local API
  +--> TermuxBridge
  +--> Wi-Fi / battery / notification / clipboard / location
```

### Repository layout

```text
core/        config, logger, memory, security, router, agent
providers/   OpenAI, Anthropic, Gemini, OpenRouter, Ollama
tools/       shell, files, network, wifi, termux, http, notes
interfaces/  CLI, FastAPI, Telegram
termux/      Termux installers and launchers
android/     Kotlin bridge, Wi-Fi scanner, notifications
flutter_app/ mobile client
tests/       pytest tests
docs/        architecture, security, roadmap and reports
deploy/      VPS deployment script, Caddy configuration and VPS docs
```

## Requirements

Python 3.10+ is supported. CI checks Python 3.10, 3.13 and 3.14.

For Android/Termux functionality, use a real Android device with Termux and Termux:API. Root is never assumed or fabricated.

For VPS production deployment, use a supported Ubuntu/Debian Linux VPS with Docker Engine and the Docker Compose plugin.

Official Docker installation references:
- https://docs.docker.com/engine/install/
- https://docs.docker.com/compose/install/linux/

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Configure only the provider credentials you actually use. No API key or token is required just to start the application and answer `/health`.

## CLI

```bash
python -m interfaces.cli
python -m mychatbot
```

The CLI uses the local/device capability profile. On Termux, the existing environment detection selects the `device` profile automatically.

## API

Run locally with:

```bash
python -m uvicorn interfaces.api_server:app --host 127.0.0.1 --port 8765
```

The application listens on `0.0.0.0` inside Docker; the host does not publish port 8765 in the production Compose stack.

### Health and readiness

```text
GET /health  -> liveness, always independent of AI provider availability
GET /ready   -> readiness, verifies the data directory and reports configured providers
```

`/health` is intentionally public so Docker and external monitors can verify the process. Protected endpoints require:

```http
Authorization: Bearer <API_TOKEN>
```

## Providers

The repository currently contains:

- OpenRouter
- OpenAI
- Anthropic
- Gemini
- Ollama

The Router only considers configured providers and normalizes timeout, credential, rate-limit, connection and invalid-request failures.

## Tool capability profiles

The registry now distinguishes runtime capabilities:

| Profile | Intended runtime | Public API tools |
|---|---|---|
| `local` | Linux development / CLI | local shell, files, network, HTTP, notes |
| `device` | Termux / Android | local tools + Termux/Wi-Fi/device tools |
| `server` | Docker / VPS API | notes/memory tools only |

The FastAPI API uses `API_TOOL_PROFILE=server` by default. Docker also sets `TOOL_PROFILE=server`.

This prevents Android/Termux commands, Wi-Fi scanning, shell execution, arbitrary file access and similar privileged capabilities from becoming public VPS endpoints.

When a tool is not supported by the current runtime, the tool registry returns a structured `capability_unavailable` result instead of faking the operation.

## Android / Termux

Existing Termux launchers remain available:

```bash
bash termux/install.sh
bash termux/start.sh
bash termux/start_api.sh
```

The Android bridge only launches the approved CLI/API bridge modes. Wi-Fi scanning checks Android permission and Wi-Fi state. BSSIDs are masked in public-facing output.

## Wi-Fi

`wifi_info` and `wifi_scan` use Termux:API on a real Android/Termux device. They are not used by the Docker/VPS runtime.

Low-level monitor mode, root-only operations and kernel-specific Wi-Fi functionality are not emulated. The application reports unavailable capabilities instead.

## Docker

### Build the production image

```bash
docker build -t mychatbot:local .
```

The image uses Python 3.13.15 slim-bookworm, installs the runtime-only dependency set, runs as UID/GID 10001, and stores persistent application data under `/data`.

No `.env`, `.git`, virtualenv, Android sources, Termux sources or test caches are copied into the image.

### Run the container

```bash
docker run --rm \
  -p 127.0.0.1:8765:8765 \
  -e API_TOKEN='replace-me' \
  -e OPENROUTER_API_KEY='replace-me' \
  -e TOOL_PROFILE=server \
  -e MYCHATBOT_DATA=/data \
  mychatbot:local
```

Health check:

```bash
curl -fsS http://127.0.0.1:8765/health
```

## Docker Compose

Production Compose is in `compose.yaml`.

It provides:

- `mychatbot` API container
- persistent `./data:/data` storage
- Caddy reverse proxy
- automatic restart
- container health checks
- non-root application execution
- no published API port

Start locally with a local image:

```bash
MYCHATBOT_IMAGE=mychatbot:local MYCHATBOT_DOMAIN=localhost docker compose up -d
```

Logs:

```bash
docker compose logs -f mychatbot
docker compose logs -f caddy
```

Stop:

```bash
docker compose down
```

The application data remains in `./data`.

## VPS Deployment

The production stack uses:

```text
GitHub -> CI -> Docker build -> GHCR -> SSH -> VPS -> Docker Compose -> Caddy -> MyChatBot
```

The VPS does not need the source repository. It stores:

```text
/opt/mychatbot/
├── .env.production
├── .current_image
├── compose.yaml
├── data/
└── deploy/
    ├── Caddyfile
    └── deploy.sh
```

See `deploy/README.md` for the complete Ubuntu/Debian bootstrap procedure, firewall setup, GHCR authentication, DNS and HTTPS configuration.

### Required GitHub production environment secrets

Create a GitHub environment named `production` and configure:

```text
VPS_HOST
VPS_PORT              # optional, defaults to 22
VPS_USER
VPS_SSH_PRIVATE_KEY
VPS_KNOWN_HOSTS
VPS_DEPLOY_PATH       # e.g. /opt/mychatbot
```

The workflow also uses GitHub's built-in `GITHUB_TOKEN` for GHCR authentication. No GHCR password is committed to the repository.

GitHub environment secrets are only available to jobs referencing that environment. You can also require manual approval for the production environment. See:
- https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

### VPS runtime environment

Create `/opt/mychatbot/.env.production` from `deploy/.env.production.example`.

Required or commonly used values:

```text
MYCHATBOT_DOMAIN
API_TOKEN
OPENROUTER_API_KEY or another selected provider key
MYCHATBOT_MASTER_KEY (optional but recommended for explicit key management)
PUBLIC_HEALTH_URL (optional)
```

Never put `.env.production` into Git.

## GitHub Actions

### CI

`.github/workflows/python-ci.yml` runs on pull requests and pushes to `main`.

It performs:

- Python 3.10/3.13/3.14 dependency installation
- syntax checks
- import checks
- shell syntax checks
- pytest

### Docker verification

`.github/workflows/docker.yml` builds the Docker image on pull requests, validates Compose, starts the container and waits for a real HTTP `/health` response.

### Production deployment

`.github/workflows/deploy.yml` is triggered after a successful CI run for `main` (and can also be run manually).

It performs:

1. checkout of the exact successful commit SHA
2. Docker build
3. real container startup and `/health` verification
4. GHCR publication with immutable commit-SHA tag plus `main`
5. SSH host-key verification
6. upload of Compose/deployment manifests to the VPS
7. deployment of that exact image SHA
8. health-gated success
9. automatic rollback to the previous known-good image if health fails

A superseded commit is skipped if a newer commit is already on `main` when the deployment workflow starts.

## HTTPS

Caddy is used for the production reverse proxy.

Set a real DNS name in:

```text
MYCHATBOT_DOMAIN=your-real-domain.example
```

Point the DNS record to the VPS public IP and allow TCP ports 80 and 443. Caddy will manage the TLS certificate automatically.

The application port 8765 stays private inside the Compose network.

## Health Checks

Container liveness:

```bash
curl -fsS http://127.0.0.1:8765/health
```

Readiness:

```bash
curl -fsS http://127.0.0.1:8765/ready
```

Public health, after DNS/HTTPS is configured:

```bash
curl -fsS https://your-real-domain.example/health
```

## Rollback

The deployment script stores the last successful image in `.current_image` and never removes the previous image as part of normal deployment.

Automatic rollback occurs when the candidate image fails its health gate.

Manual rollback:

```bash
cd /opt/mychatbot
PREVIOUS_IMAGE="$(head -n 1 .current_image)"
DEPLOY_DIR=/opt/mychatbot IMAGE_REF="$PREVIOUS_IMAGE" ./deploy/deploy.sh
```

## Environment Variables

The complete development template is `.env.example`.

The complete VPS template is `deploy/.env.production.example`.

Supported provider variables are only required for the provider selected by the Router. Unconfigured providers are skipped by fallback selection.

## Persistent Storage

The application stores its SQLite memory database and generated master key under `MYCHATBOT_DATA`.

Docker maps that path to `/data`, backed by the persistent VPS directory `/opt/mychatbot/data`.

Do not delete this directory unless you intentionally want to remove application memory and the generated master key.

## Security

- no secrets in images or Git
- no `.env` files committed
- production API uses `API_TOOL_PROFILE=server`
- shell execution remains disabled by default
- Docker application runs as non-root UID/GID 10001
- container drops Linux capabilities and enables `no-new-privileges`
- API port is not publicly published in Compose
- Caddy is the only public application entry point
- logs use redaction helpers for sensitive values
- Android/Termux capabilities are never faked on VPS
- SSH host keys are verified by `VPS_KNOWN_HOSTS`

## Testing

Run locally:

```bash
python -m pip install -r requirements.txt
pytest -q
```

Build and start Docker:

```bash
docker build -t mychatbot:local .
docker run -d --name mychatbot-local -p 127.0.0.1:8765:8765 -e TOOL_PROFILE=server -e MYCHATBOT_DATA=/data mychatbot:local
curl -fsS http://127.0.0.1:8765/health
docker rm -f mychatbot-local
```

On a real Android device, also validate Termux API and Android permissions. Those checks cannot be honestly substituted by a Linux CI runner.

## Troubleshooting

**`API provider is not configured`** — configure one supported provider or make a local Ollama server available.

**`API_TOKEN is not configured`** — protected API endpoints intentionally return HTTP 503 until you configure an API token.

**`capability_unavailable`** — the requested tool belongs to Android/Termux/local-only capabilities and the current runtime is the VPS `server` profile.

**Container is unhealthy** — inspect:

```bash
docker compose logs --tail=200 mychatbot
docker inspect mychatbot --format '{{json .State.Health}}'
```

**HTTPS does not issue a certificate** — verify DNS points to the VPS and TCP 80/443 are reachable.

**Deployment failed** — inspect the deployment workflow logs. The VPS script should restore the previous known-good image after a failed health gate.

## Dependency Policy

Runtime dependencies are pinned in `requirements-prod.txt` and `pyproject.toml`. Test dependencies remain in `requirements.txt`.

The production image uses Python 3.13.15 slim-bookworm and installs only the runtime set. No Rust toolchain is placed in the final image.
