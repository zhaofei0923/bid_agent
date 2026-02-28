#!/usr/bin/env bash
# BidAgent V2 — First-time server setup script
# Run on Tencent Cloud server as the deploy user (ubuntu).
# Usage: bash deploy/setup-server.sh
set -euo pipefail

DOMAIN="bid.easudata.com"
PROJECT_DIR="/opt/bid_agent"
COMPOSE_FILE="docker-compose.prod.yml"

echo "=========================================="
echo " BidAgent V2 — Server Setup"
echo "=========================================="

# ── 1. Swap (skip if already exists) ─────────────────
if ! swapon --show | grep -q '/swapfile'; then
    echo ">>> Creating 2GB swap..."
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "    Swap created."
else
    echo ">>> Swap already exists, skipping."
fi

# ── 2. Project directory ─────────────────────────────
echo ">>> Ensuring project directory ${PROJECT_DIR}..."
sudo mkdir -p "${PROJECT_DIR}"
sudo chown "$(whoami):$(whoami)" "${PROJECT_DIR}"

# ── 3. Docker cleanup ────────────────────────────────
echo ">>> Cleaning unused Docker resources..."
docker system prune -f
docker builder prune -f

# ── 4. Clone or update repo ──────────────────────────
if [ -d "${PROJECT_DIR}/.git" ]; then
    echo ">>> Repo exists, pulling latest..."
    cd "${PROJECT_DIR}"
    git pull origin main
else
    echo ">>> Cloning repository..."
    git clone git@github.com:zhaofei0923/bid_agent.git "${PROJECT_DIR}"
    cd "${PROJECT_DIR}"
fi

# ── 5. Environment file ──────────────────────────────
if [ ! -f "${PROJECT_DIR}/.env" ]; then
    echo ">>> Creating .env from template..."
    cp "${PROJECT_DIR}/.env.production.example" "${PROJECT_DIR}/.env"

    # Generate random secrets
    SECRET_KEY=$(openssl rand -hex 32)
    JWT_SECRET=$(openssl rand -hex 32)
    DB_PASSWORD=$(openssl rand -hex 16)

    sed -i "s|REPLACE_WITH_openssl_rand_hex_32|${SECRET_KEY}|" "${PROJECT_DIR}/.env"
    # Fix: sed can only replace first match, do JWT separately
    sed -i "s|REPLACE_WITH_openssl_rand_hex_32|${JWT_SECRET}|" "${PROJECT_DIR}/.env"
    sed -i "s|REPLACE_STRONG_DB_PASSWORD|${DB_PASSWORD}|g" "${PROJECT_DIR}/.env"

    echo "    .env created with random secrets."
    echo "    ⚠️  Edit .env to fill in LLM_API_KEY, HUNYUAN_SECRET_ID/KEY, ZHIPU_API_KEY"
else
    echo ">>> .env already exists, skipping."
fi

# ── 6. SSL certificate ───────────────────────────────
if [ ! -d "/etc/letsencrypt/live/${DOMAIN}" ]; then
    echo ">>> Requesting SSL certificate for ${DOMAIN}..."
    # Use webroot if nginx is running, standalone otherwise
    if systemctl is-active --quiet nginx; then
        sudo certbot certonly --webroot -w /var/www/html -d "${DOMAIN}" --non-interactive --agree-tos --email admin@easudata.com
    else
        sudo certbot certonly --standalone -d "${DOMAIN}" --non-interactive --agree-tos --email admin@easudata.com
    fi
    echo "    SSL certificate obtained."
else
    echo ">>> SSL certificate already exists for ${DOMAIN}."
fi

# ── 7. Nginx configuration ───────────────────────────
echo ">>> Installing Nginx config..."
sudo cp "${PROJECT_DIR}/deploy/nginx-bid.conf" "/etc/nginx/sites-available/bid"
sudo ln -sf "/etc/nginx/sites-available/bid" "/etc/nginx/sites-enabled/bid"
sudo nginx -t
sudo systemctl reload nginx
echo "    Nginx configured and reloaded."

# ── 8. Login to GHCR ─────────────────────────────────
echo ">>> Logging in to GitHub Container Registry..."
echo "    If prompted, enter your GitHub Personal Access Token (with packages:read scope)."
docker login ghcr.io -u zhaofei0923

# ── 9. Start services ────────────────────────────────
echo ">>> Pulling images and starting services..."
cd "${PROJECT_DIR}"
docker compose -f "${COMPOSE_FILE}" pull
docker compose -f "${COMPOSE_FILE}" up -d

# ── 10. Wait for services, then migrate ──────────────
echo ">>> Waiting for backend to be ready..."
sleep 10
docker compose -f "${COMPOSE_FILE}" exec -T backend alembic upgrade head

echo ""
echo "=========================================="
echo " ✅ BidAgent V2 deployed successfully!"
echo ""
echo " Frontend:  https://${DOMAIN}"
echo " API:       https://${DOMAIN}/v1/health"
echo ""
echo " Next steps:"
echo "   1. Edit .env to add API keys (LLM, Embedding)"
echo "   2. Configure GitHub Secrets for CI/CD"
echo "   3. Restart: docker compose -f ${COMPOSE_FILE} restart"
echo "=========================================="
