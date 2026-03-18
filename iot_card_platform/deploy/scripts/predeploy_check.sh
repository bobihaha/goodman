#!/usr/bin/env bash

set -euo pipefail

echo "[1/5] Checking required files"
test -f .env.production
test -f docker-compose.prod.yml

echo "[2/5] Checking Docker"
docker --version >/dev/null
docker compose version >/dev/null

echo "[3/5] Checking compose config"
docker compose -f docker-compose.prod.yml config >/dev/null

echo "[4/5] Checking free disk space"
df -h .

echo "[5/5] Planned containers"
docker compose -f docker-compose.prod.yml ps || true

echo "Predeploy check passed"
