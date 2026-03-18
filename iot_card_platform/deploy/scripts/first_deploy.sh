#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

cd "${PROJECT_ROOT}"

mkdir -p logs backups/mysql backups/redis

if [ ! -f .env.production ]; then
  cp .env.production.example .env.production
  echo "Created .env.production from template. Please edit it before continuing."
  exit 1
fi

echo "[1/4] Running predeploy checks"
bash deploy/scripts/predeploy_check.sh

echo "[2/4] Building and starting containers"
docker compose -f docker-compose.prod.yml up -d --build

echo "[3/4] Waiting for services"
sleep 10

echo "[4/4] Running health check"
bash deploy/scripts/health_check.sh

echo "First deploy completed"
