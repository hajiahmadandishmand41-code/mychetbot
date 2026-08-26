# VPS deployment

This deployment intentionally runs only the FastAPI server path. Android, Termux, Wi-Fi scan, notification, clipboard, location and shell/file tools are not exposed by the public API profile.

## 1. Prepare Ubuntu/Debian VPS

Use a dedicated non-root deployment account. The initial account setup requires an administrator once; GitHub Actions then logs in only as the deployment user.

```bash
sudo useradd --create-home --shell /bin/bash mychatdeploy
sudo passwd -l mychatdeploy
sudo usermod -aG docker mychatdeploy
sudo install -d -o mychatdeploy -g mychatdeploy -m 750 /opt/mychatbot
sudo install -d -o mychatdeploy -g mychatdeploy -m 750 /opt/mychatbot/data
sudo install -d -o mychatdeploy -g mychatdeploy -m 750 /opt/mychatbot/deploy
sudo chown 10001:10001 /opt/mychatbot/data
```

The Docker group gives a user effective control over the Docker daemon, so the SSH account is non-root but still host-privileged through Docker. Do not reuse this account for interactive application work.

Install Docker Engine from Docker's official apt repository and install the Compose plugin. Docker currently documents Ubuntu 22.04, 24.04 and 26.04 LTS as supported releases.

- Docker Engine: https://docs.docker.com/engine/install/ubuntu/
- Docker Compose plugin: https://docs.docker.com/compose/install/linux/

```bash
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
sudo tee /etc/apt/sources.list.d/docker.sources >/dev/null <<EOF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Architectures: $(dpkg --print-architecture)
Signed-By: /etc/apt/keyrings/docker.asc
EOF
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo systemctl enable --now docker
sudo -iu mychatdeploy docker run --rm hello-world
sudo -iu mychatdeploy docker compose version
```

## 2. Firewall

Allow only SSH and public web traffic. Keep application port 8765 private because Compose does not publish it to the host.

```bash
sudo apt install -y ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status verbose
```

Docker-published ports can interact with host firewall rules in ways that require care; this stack publishes only Caddy's 80/443 ports and keeps the API internal to the Compose network.

## 3. Production environment file

Create the environment file on the VPS. Never commit it.

```bash
sudo -u mychatdeploy cp /opt/mychatbot/deploy/.env.production.example /opt/mychatbot/.env.production
sudo -u mychatdeploy nano /opt/mychatbot/.env.production
sudo chmod 600 /opt/mychatbot/.env.production
sudo chown mychatdeploy:mychatdeploy /opt/mychatbot/.env.production
```

Set a real DNS name in `MYCHATBOT_DOMAIN`, a strong `API_TOKEN`, and only the AI provider key you intend to use. Store a stable `MYCHATBOT_MASTER_KEY` here or let the application create `/opt/mychatbot/data/.master.key` on first startup.

For a private GHCR package, authenticate the deployment user once using a token with only package-read access:

```bash
echo '<GHCR_READ_TOKEN>' | docker login ghcr.io -u '<GHCR_USERNAME>' --password-stdin
```

Do not put that token in GitHub workflow files or the repository.

## 4. DNS and HTTPS

Point the chosen DNS record (for example `bot.example.com`) to the VPS public IP. Caddy will request and renew the TLS certificate automatically when ports 80 and 443 are reachable. The repository contains no hard-coded domain.

## 5. First deployment

The GitHub Actions deployment job creates `/opt/mychatbot/deploy`, uploads the current `compose.yaml`, `Caddyfile`, and `deploy.sh`, then deploys the exact commit-SHA image.

Required GitHub production environment values:

- `VPS_HOST`
- `VPS_PORT` (optional; defaults to 22)
- `VPS_USER`
- `VPS_SSH_PRIVATE_KEY`
- `VPS_KNOWN_HOSTS`
- `VPS_DEPLOY_PATH` (for example `/opt/mychatbot`)

Store them in the GitHub `production` environment. Environment secrets are only exposed to jobs that reference that environment; production can also be protected with required reviewers.

`VPS_KNOWN_HOSTS` must contain the verified SSH host-key line(s) for the VPS. Do not let CI silently accept an unknown host key.

## 6. Runtime checks

```bash
cd /opt/mychatbot
docker compose --env-file .env.production ps
docker compose --env-file .env.production logs --tail=100 mychatbot
curl -fsS http://127.0.0.1:8765/health
```

The public check, when configured, is:

```bash
curl -fsS https://YOUR_REAL_DOMAIN/health
```

## 7. Manual deployment

For a manual release, keep the image immutable and pass the full GHCR image reference:

```bash
cd /opt/mychatbot
DEPLOY_DIR=/opt/mychatbot IMAGE_REF=ghcr.io/OWNER/mychetbot:COMMIT_SHA ./deploy/deploy.sh
```

The script records the last successful image in `.current_image`, waits for the container health check, optionally verifies the public HTTPS URL, and does not mark the candidate successful until health passes.

## 8. Rollback

The deployment script automatically restores the previous image when the new image fails startup or health checks.

Manual rollback:

```bash
cd /opt/mychatbot
PREVIOUS_IMAGE="$(head -n 1 .current_image)"
# Replace PREVIOUS_IMAGE with the known-good SHA you want to restore.
DEPLOY_DIR=/opt/mychatbot IMAGE_REF="$PREVIOUS_IMAGE" ./deploy/deploy.sh
```

Do not delete old images immediately. They are required for fast rollback. Perform image cleanup only after a newer release has been verified and retention is acceptable.

## 9. Logs

```bash
docker compose --env-file .env.production logs -f mychatbot
docker compose --env-file .env.production logs -f caddy
```

The application logs are stdout/stderr based. Secrets and authorization headers must not be copied into log statements.
