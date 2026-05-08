#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

cd "${PROJECT_ROOT}"

echo "[1/6] Containers"
docker compose -f docker-compose.prod.yml ps

echo "[2/6] Backend health"
curl -fsS http://127.0.0.1/health
echo

echo "[3/6] Nginx health"
curl -fsS http://127.0.0.1/healthz
echo

echo "[4/6] MySQL ping"
docker exec iot_mysql sh -lc 'exec mysqladmin -uroot -p"$MYSQL_ROOT_PASSWORD" ping'

echo "[5/6] Redis ping"
docker exec iot_redis redis-cli ping

echo "[6/6] Recent backend logs"
docker logs iot_backend --tail 50

echo "Health check passed"
