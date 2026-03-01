#!/usr/bin/env bash
# BidAgent V2 — Install nginx sites and ensure TLS is available.
# Safe to run repeatedly. This keeps the server's nginx state aligned with the
# deployment assets committed in the repo.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOMAIN="${BID_DOMAIN:-bid.easudata.com}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-admin@easudata.com}"
WEBROOT="${BID_WEBROOT:-/var/www/html}"

BID_SITE_SRC="${PROJECT_DIR}/deploy/nginx-bid.conf"
CATCHALL_SITE_SRC="${PROJECT_DIR}/deploy/nginx-default-catchall.conf"
BID_SITE_DST="/etc/nginx/sites-available/bid"
CATCHALL_SITE_DST="/etc/nginx/sites-available/000-default-catchall"
CERT_DIR="/etc/letsencrypt/live/${DOMAIN}"

ensure_prerequisites() {
    if ! command -v nginx >/dev/null 2>&1; then
        echo "nginx is required but not installed" >&2
        exit 1
    fi

    if ! command -v certbot >/dev/null 2>&1; then
        echo "certbot is required but not installed" >&2
        exit 1
    fi
}

reload_or_start_nginx() {
    if sudo systemctl is-active --quiet nginx; then
        sudo systemctl reload nginx
    else
        sudo systemctl start nginx
    fi
}

install_bootstrap_http_site() {
    sudo mkdir -p "${WEBROOT}/.well-known/acme-challenge"

    sudo tee "${BID_SITE_DST}" >/dev/null <<EOF
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root ${WEBROOT};
    }

    location / {
        return 404;
    }
}
EOF

    sudo ln -sfn "${BID_SITE_DST}" /etc/nginx/sites-enabled/bid
    sudo nginx -t
    reload_or_start_nginx
}

ensure_certificate() {
    if [ -d "${CERT_DIR}" ]; then
        echo ">>> SSL certificate already exists for ${DOMAIN}."
        return
    fi

    echo ">>> Requesting SSL certificate for ${DOMAIN}..."

    if sudo systemctl is-active --quiet nginx; then
        install_bootstrap_http_site
        sudo certbot certonly \
            --webroot \
            -w "${WEBROOT}" \
            -d "${DOMAIN}" \
            --non-interactive \
            --agree-tos \
            --email "${CERTBOT_EMAIL}"
    else
        sudo certbot certonly \
            --standalone \
            -d "${DOMAIN}" \
            --non-interactive \
            --agree-tos \
            --email "${CERTBOT_EMAIL}"
    fi

    echo "    SSL certificate obtained."
}

install_final_sites() {
    echo ">>> Installing nginx site configs..."
    sudo cp "${BID_SITE_SRC}" "${BID_SITE_DST}"
    sudo cp "${CATCHALL_SITE_SRC}" "${CATCHALL_SITE_DST}"

    sudo ln -sfn "${BID_SITE_DST}" /etc/nginx/sites-enabled/bid
    sudo ln -sfn "${CATCHALL_SITE_DST}" /etc/nginx/sites-enabled/000-default-catchall

    sudo nginx -t
    reload_or_start_nginx
    echo "    Nginx configured and reloaded."
}

ensure_prerequisites
ensure_certificate
install_final_sites
