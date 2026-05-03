#!/usr/bin/env bash
set -u

STATUS_FILE="/tmp/bid_agent_deploy.status"
LOG_PREFIX="[remote-deploy]"

mark_failed() {
  echo "failed" > "$STATUS_FILE"
}

fail() {
  echo "$LOG_PREFIX FAILED: $1"
  mark_failed
  exit 1
}

set_env_value() {
  local key="$1"
  local value="$2"

  if grep -q "^${key}=" .env; then
    sed -i "s|^${key}=.*|${key}=${value}|" .env || fail "set ${key}"
  else
    printf '\n%s=%s\n' "$key" "$value" >> .env || fail "append ${key}"
  fi
}

trap 'mark_failed' ERR

echo "running" > "$STATUS_FILE"
echo "$LOG_PREFIX started at $(date)"

cd /opt/bid_agent || fail "cannot cd /opt/bid_agent"

echo "$LOG_PREFIX Step 1/6: ensure env and directories"
mkdir -p data/uploads
if [ ! -f .env ]; then
  cp .env.production.example .env || fail "copy .env template"
  SECRET_KEY=$(openssl rand -hex 32)
  JWT_SECRET=$(openssl rand -hex 32)
  DB_PASS=$(openssl rand -hex 16)
  sed -i "0,/REPLACE_WITH_openssl_rand_hex_32/s//$SECRET_KEY/" .env || fail "set SECRET_KEY"
  sed -i "0,/REPLACE_WITH_openssl_rand_hex_32/s//$JWT_SECRET/" .env || fail "set JWT_SECRET"
  sed -i "s/REPLACE_STRONG_DB_PASSWORD/$DB_PASS/g" .env || fail "set DB password"
  echo "$LOG_PREFIX .env created"
else
  echo "$LOG_PREFIX .env exists"
fi
set_env_value "LLM_MODEL" "deepseek-v4-pro"
set_env_value "LLM_REASONING_MODEL" "deepseek-v4-pro"

echo "$LOG_PREFIX Step 2/6: configure nginx"
bash deploy/install-nginx-sites.sh || fail "nginx config"

echo "$LOG_PREFIX Step 3/6: build images locally"
docker compose -f docker-compose.prod.yml build --progress=plain backend frontend || fail "docker compose build"

echo "$LOG_PREFIX Step 4/6: restart containers"
docker compose -f docker-compose.prod.yml down --remove-orphans || true
docker compose -f docker-compose.prod.yml up -d --remove-orphans || fail "docker compose up"
docker compose -f docker-compose.prod.yml ps -a

echo "$LOG_PREFIX Step 5/6: run migration"
sleep 15
docker compose -f docker-compose.prod.yml run --rm backend python -m alembic upgrade head || fail "alembic migration"

echo "$LOG_PREFIX Step 6/6: cleanup"
docker image prune -f > /dev/null 2>&1 || true

echo "success" > "$STATUS_FILE"
echo "$LOG_PREFIX success at $(date)"
