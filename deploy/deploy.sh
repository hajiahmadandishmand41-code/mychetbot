#!/usr/bin/env bash
set -Eeuo pipefail

DEPLOY_DIR="${DEPLOY_DIR:-/opt/mychatbot}"
IMAGE_REF="${IMAGE_REF:-}"
COMPOSE=(docker compose --env-file "$DEPLOY_DIR/.env.production")
CURRENT_FILE="$DEPLOY_DIR/.current_image"

fail() {
  echo "[deploy] ERROR: $*" >&2
  exit 1
}

[[ -n "$IMAGE_REF" ]] || fail "IMAGE_REF is required"
[[ -f "$DEPLOY_DIR/compose.yaml" ]] || fail "compose.yaml not found in $DEPLOY_DIR"
[[ -f "$DEPLOY_DIR/.env.production" ]] || fail ".env.production not found in $DEPLOY_DIR"
command -v docker >/dev/null || fail "docker is not installed or not in PATH"
docker compose version >/dev/null 2>&1 || fail "Docker Compose plugin is unavailable"

mkdir -p "$DEPLOY_DIR/data"
chmod 750 "$DEPLOY_DIR/data" || true

previous_image=""
if [[ -f "$CURRENT_FILE" ]]; then
  previous_image="$(head -n 1 "$CURRENT_FILE" | tr -d '\r\n')"
fi

wait_for_health() {
  local image_ref="$1" tries=0 status cid
  while (( tries < 60 )); do
    cid="$(IMAGE_REF="$image_ref" "${COMPOSE[@]}" ps -q mychatbot)"
    if [[ -n "$cid" ]]; then
      status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}starting{{end}}' "$cid" 2>/dev/null || true)"
      case "$status" in
        healthy) return 0 ;;
        unhealthy) return 1 ;;
      esac
    fi
    sleep 2
    tries=$((tries + 1))
  done
  return 1
}

echo "[deploy] pulling $IMAGE_REF"
if ! IMAGE_REF="$IMAGE_REF" "${COMPOSE[@]}" pull mychatbot; then
  fail "failed to pull candidate image"
fi

echo "[deploy] starting candidate"
if ! IMAGE_REF="$IMAGE_REF" "${COMPOSE[@]}" up -d mychatbot caddy; then
  if [[ -n "$previous_image" ]]; then
    echo "[deploy] startup failed; rolling back to $previous_image"
    IMAGE_REF="$previous_image" "${COMPOSE[@]}" up -d mychatbot caddy || true
  fi
  fail "candidate deployment failed"
fi

if ! wait_for_health "$IMAGE_REF"; then
  echo "[deploy] health check failed"
  if [[ -n "$previous_image" ]]; then
    echo "[deploy] restoring previous known-good image: $previous_image"
    IMAGE_REF="$previous_image" "${COMPOSE[@]}" up -d mychatbot caddy
    IMAGE_REF="$previous_image" "${COMPOSE[@]}" ps
    if wait_for_health "$previous_image"; then
      echo "[deploy] rollback succeeded; deployment remains failed"
    else
      echo "[deploy] rollback health check FAILED" >&2
    fi
  else
    echo "[deploy] no previous release recorded; service may require manual recovery" >&2
  fi
  exit 1
fi

if [[ -n "${PUBLIC_HEALTH_URL:-}" ]]; then
  command -v curl >/dev/null || fail "curl is required when PUBLIC_HEALTH_URL is configured"
  if ! curl --fail --silent --show-error --max-time 15 "$PUBLIC_HEALTH_URL" >/dev/null; then
    echo "[deploy] public health check failed"
    if [[ -n "$previous_image" ]]; then
      IMAGE_REF="$previous_image" "${COMPOSE[@]}" up -d mychatbot caddy
      wait_for_health "$previous_image" || true
    fi
    exit 1
  fi
fi

printf '%s\n' "$IMAGE_REF" > "$CURRENT_FILE"
chmod 640 "$CURRENT_FILE" || true
IMAGE_REF="$IMAGE_REF" "${COMPOSE[@]}" ps

echo "[deploy] deployment succeeded: $IMAGE_REF"
